import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# SAFE IMPORTS
# ==========================================================

try:
    from core.quant_models import add_indicators, quant_stack
except Exception:
    add_indicators = None
    quant_stack = None

try:
    from core.data_connectors import manual_connect
except Exception:
    manual_connect = None

try:
    from core.database import append_csv
except Exception:
    append_csv = None

try:
    from tabs.backtest import advanced_last120_similarity_engine as _backtest_similarity_engine
except Exception:
    _backtest_similarity_engine = None


# ==========================================================
# SAFE BASIC HELPERS
# ==========================================================

def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        value = float(value)
        if not np.isfinite(value):
            return default
        return value
    except Exception:
        return default


def _safe_round(value, digits=2, default=0.0):
    try:
        return round(_safe_float(value, default), digits)
    except Exception:
        return default


def _safe_session_get(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def _safe_append_csv(name, row):
    if append_csv is None:
        return False, "append_csv is unavailable."

    try:
        append_csv(name, row)
        return True, "Saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _normalize_ohlc(df):
    """
    Make sure the dashboard has safe time/open/high/low/close columns.
    """
    if df is None:
        return pd.DataFrame()

    try:
        work = df.copy()
    except Exception:
        return pd.DataFrame()

    if work.empty:
        return pd.DataFrame()

    rename_map = {}
    for col in work.columns:
        lc = str(col).lower().strip()

        if lc in ["datetime", "date", "timestamp"]:
            rename_map[col] = "time"
        elif lc == "o":
            rename_map[col] = "open"
        elif lc == "h":
            rename_map[col] = "high"
        elif lc == "l":
            rename_map[col] = "low"
        elif lc == "c":
            rename_map[col] = "close"

    if rename_map:
        work = work.rename(columns=rename_map)

    if "time" not in work.columns:
        if isinstance(work.index, pd.DatetimeIndex):
            work = work.reset_index().rename(columns={"index": "time"})
        else:
            work["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(work), freq="1min")

    work["time"] = pd.to_datetime(work["time"], errors="coerce")

    if "close" not in work.columns:
        return pd.DataFrame()

    work["close"] = pd.to_numeric(work["close"], errors="coerce").ffill().bfill()

    if "open" not in work.columns:
        work["open"] = work["close"].shift(1).fillna(work["close"])

    if "high" not in work.columns:
        work["high"] = work[["open", "close"]].max(axis=1)

    if "low" not in work.columns:
        work["low"] = work[["open", "close"]].min(axis=1)

    for col in ["open", "high", "low", "close"]:
        work[col] = pd.to_numeric(work[col], errors="coerce").ffill().bfill()

    work = work.dropna(subset=["time", "open", "high", "low", "close"]).reset_index(drop=True)

    return work


def _safe_add_indicators(df):
    """
    Run your original add_indicators if available.
    If it fails, keep OHLC and add fallback indicator columns.
    """
    work = _normalize_ohlc(df)

    if work.empty:
        return pd.DataFrame()

    if add_indicators is not None:
        try:
            dfi = add_indicators(work)
            dfi = _normalize_ohlc(dfi)

            if not dfi.empty:
                work = dfi
        except Exception:
            pass

    work = work.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0)

    # Fallback indicators if your core indicator engine misses any column
    close = pd.to_numeric(work["close"], errors="coerce").ffill().bfill()
    high = pd.to_numeric(work["high"], errors="coerce").ffill().bfill()
    low = pd.to_numeric(work["low"], errors="coerce").ffill().bfill()

    if "atr" not in work.columns:
        tr = (high - low).abs()
        work["atr"] = tr.rolling(14, min_periods=1).mean()

    if "volatility" not in work.columns:
        work["volatility"] = close.pct_change().rolling(30, min_periods=1).std().fillna(0)

    if "adx" not in work.columns:
        candle_range = (high - low).abs()
        avg_range = candle_range.rolling(14, min_periods=1).mean()
        work["adx"] = np.clip((avg_range / close.abs().replace(0, np.nan) * 10000).fillna(0), 0, 60)

    if "plus_di" not in work.columns:
        work["plus_di"] = np.where(close.diff().fillna(0) > 0, 25, 10)

    if "minus_di" not in work.columns:
        work["minus_di"] = np.where(close.diff().fillna(0) < 0, 25, 10)

    if "pressure" not in work.columns:
        work["pressure"] = pd.to_numeric(work["plus_di"], errors="coerce").fillna(0) - pd.to_numeric(work["minus_di"], errors="coerce").fillna(0)

    if "mean_dist" not in work.columns:
        ma = close.rolling(50, min_periods=1).mean()
        atr = pd.to_numeric(work["atr"], errors="coerce").replace(0, np.nan).ffill().bfill().fillna(1)
        work["mean_dist"] = ((close - ma) / atr).fillna(0)

    if "fat_tail" not in work.columns:
        ret = close.pct_change().fillna(0)
        work["fat_tail"] = np.clip(ret.abs().rolling(30, min_periods=1).mean() * 10000, 0, 100)

    if "adx_slope" not in work.columns:
        work["adx_slope"] = pd.to_numeric(work["adx"], errors="coerce").diff().fillna(0)

    if "momentum" not in work.columns:
        work["momentum"] = close.diff(10).fillna(0)

    if "vol_decay" not in work.columns:
        vol = pd.to_numeric(work["volatility"], errors="coerce").fillna(0)
        work["vol_decay"] = vol.diff().fillna(0) * -1

    for col in work.columns:
        if col != "time":
            try:
                work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
            except Exception:
                pass

    return work.reset_index(drop=True)


# ==========================================================
# SAFE QUANT STACK
# ==========================================================

def _fallback_quant_stack(dfi):
    """
    Backup decision engine if core.quant_stack crashes.
    This keeps the dashboard alive.
    """
    if dfi is None or dfi.empty:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
            "adx": 0,
            "pressure": 0,
            "ml_conf_pct": 0,
            "history_match_pct": 0,
            "mean_revert_risk_pct": 100,
            "fat_tail_risk_pct": 100,
            "spoofing_risk_pct": 100,
            "ergodicity_pct": 0,
            "monte_carlo_pct": 0,
        }

    last = dfi.iloc[-1]

    adx = _safe_float(last.get("adx", 0))
    pressure = _safe_float(last.get("pressure", 0))
    mean_dist = abs(_safe_float(last.get("mean_dist", 0)))
    fat_tail = abs(_safe_float(last.get("fat_tail", 0)))
    volatility = abs(_safe_float(last.get("volatility", 0)))

    if pressure > 5 and adx >= 18:
        bias = "BUY"
    elif pressure < -5 and adx >= 18:
        bias = "SELL"
    else:
        bias = "WAIT"

    trend_score = np.clip(adx / 35 * 100, 0, 100)
    pressure_score = np.clip(abs(pressure) / 25 * 100, 0, 100)
    mean_risk = np.clip(mean_dist * 18, 0, 100)
    fat_risk = np.clip(fat_tail, 0, 100)
    spoof_risk = np.clip(max(0, fat_risk - pressure_score * 0.25), 0, 100)

    safe_pct = (
        trend_score * 0.30
        + pressure_score * 0.30
        + (100 - mean_risk) * 0.20
        + (100 - fat_risk) * 0.10
        + (100 - spoof_risk) * 0.10
    )

    safe_pct = float(np.clip(safe_pct, 0, 100))

    return {
        "bias": bias,
        "scale10": round(safe_pct / 10, 2),
        "safe_pct": round(safe_pct, 2),
        "adx": round(adx, 2),
        "pressure": round(pressure, 2),
        "ml_conf_pct": round(np.clip((trend_score + pressure_score) / 2, 0, 100), 2),
        "history_match_pct": round(np.clip(safe_pct * 0.85, 0, 100), 2),
        "mean_revert_risk_pct": round(mean_risk, 2),
        "fat_tail_risk_pct": round(fat_risk, 2),
        "spoofing_risk_pct": round(spoof_risk, 2),
        "ergodicity_pct": round(np.clip(100 - volatility * 10000, 0, 100), 2),
        "monte_carlo_pct": round(np.clip(safe_pct * 0.90, 0, 100), 2),
    }


def _safe_quant_stack(df, dfi):
    if quant_stack is not None:
        try:
            q = quant_stack(
                df,
                _safe_session_get("trade_history", []),
                _safe_session_get("account_snapshot", {}),
            )

            if isinstance(q, dict):
                fallback = _fallback_quant_stack(dfi)
                fallback.update(q)

                # Make sure important keys always exist
                for key, value in _fallback_quant_stack(dfi).items():
                    fallback.setdefault(key, value)

                return fallback
        except Exception:
            pass

    return _fallback_quant_stack(dfi)


# ==========================================================
# THRESHOLD / STATUS HELPERS
# ==========================================================

def _status_for_metric(name, value, bias=None):
    try:
        v = float(value)
    except Exception:
        return "UNKNOWN", "Need more data"

    n = str(name).lower()

    if "safety" in n or "safe" in n:
        if v >= 75:
            return "VERY GOOD", "High safety; still wait for entry rules"
        if v >= 58:
            return "GOOD", "Acceptable, use normal risk"
        if v >= 42:
            return "BAD", "Weak edge; reduce size or wait"
        return "DANGEROUS", "Low safety; avoid forcing trade"

    if n == "adx":
        if v >= 55:
            return "DANGEROUS", "Very strong/exhausted trend risk"
        if v >= 28:
            return "VERY GOOD", "Strong trend regime"
        if v >= 18:
            return "GOOD", "Trend building"
        return "BAD", "Weak/sideways regime"

    if "pressure" in n:
        av = abs(v)
        if av >= 28:
            return "DANGEROUS", "Extreme pressure; reversal/wick risk"
        if av >= 14:
            return "VERY GOOD", "Clear directional pressure"
        if av >= 6:
            return "GOOD", "Moderate pressure"
        return "BAD", "No clear pressure"

    if "mean" in n or "revert" in n:
        if v <= 30:
            return "VERY GOOD", "Low mean-reversion danger"
        if v <= 50:
            return "GOOD", "Manageable pullback risk"
        if v <= 70:
            return "BAD", "Pullback risk rising"
        return "DANGEROUS", "High snap-back/reversal risk"

    if "fat" in n:
        if v <= 25:
            return "VERY GOOD", "Normal tail risk"
        if v <= 45:
            return "GOOD", "Some tail risk"
        if v <= 65:
            return "BAD", "Wick/news risk rising"
        return "DANGEROUS", "Extreme tail/wick risk"

    if "spoof" in n:
        if v <= 20:
            return "VERY GOOD", "Clean pressure"
        if v <= 40:
            return "GOOD", "Acceptable noise"
        if v <= 65:
            return "BAD", "Possible fake pressure"
        return "DANGEROUS", "High fake-move risk"

    if "ergodicity" in n:
        if v >= 70:
            return "VERY GOOD", "Stable regime quality"
        if v >= 50:
            return "GOOD", "Acceptable regime quality"
        if v >= 35:
            return "BAD", "Unstable regime"
        return "DANGEROUS", "Very unstable regime"

    if "monte" in n or "ml" in n or "history" in n:
        if v >= 75:
            return "VERY GOOD", "Strong model agreement"
        if v >= 58:
            return "GOOD", "Acceptable model agreement"
        if v >= 42:
            return "BAD", "Weak model agreement"
        return "DANGEROUS", "Low model agreement"

    if "atr" in n or "volatility" in n:
        if v <= 0:
            return "UNKNOWN", "No volatility value"
        return "GOOD", "Use with symbol-specific context"

    return "GOOD", "Normal"


def _metric_with_status(col, label, value, status=None, note=None):
    if status is None or note is None:
        status, note = _status_for_metric(label, value)

    col.metric(label, value)
    col.caption(f"{status}: {note}")


def _threshold_table(q):
    rows = []

    checks = [
        ("Safety %", q.get("safe_pct", 0)),
        ("ADX", q.get("adx", 0)),
        ("Pressure", q.get("pressure", 0)),
        ("Mean Revert Risk %", q.get("mean_revert_risk_pct", 0)),
        ("Fat Tail Risk %", q.get("fat_tail_risk_pct", 0)),
        ("Spoofing Risk %", q.get("spoofing_risk_pct", 0)),
        ("Ergodicity %", q.get("ergodicity_pct", 0)),
        ("Monte Carlo %", q.get("monte_carlo_pct", 0)),
        ("ML Confidence %", q.get("ml_conf_pct", 0)),
        ("History Match %", q.get("history_match_pct", 0)),
    ]

    for metric, value in checks:
        status, note = _status_for_metric(metric, value, q.get("bias"))

        rows.append({
            "Data": metric,
            "Value": value,
            "Threshold": status,
            "Meaning": note,
        })

    return pd.DataFrame(rows)


def _compact_latest_data(dfi):
    if dfi is None or dfi.empty:
        return pd.DataFrame()

    cols = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "adx",
        "plus_di",
        "minus_di",
        "pressure",
        "atr",
        "volatility",
        "mean_dist",
        "fat_tail",
        "adx_slope",
        "momentum",
    ]

    use = [c for c in cols if c in dfi.columns]

    if not use:
        return pd.DataFrame()

    out = dfi[use].tail(80).copy()

    for c in out.columns:
        if c != "time":
            out[c] = pd.to_numeric(out[c], errors="coerce").round(5)

    return out


# ==========================================================
# SAFE CONNECT
# ==========================================================

def _safe_manual_connect(source, symbol, api_key, bars, timeframe):
    if manual_connect is None:
        st.error("manual_connect is unavailable. Check core.data_connectors import.")
        return

    try:
        with st.spinner(f"Connecting {source.upper()} {symbol} {timeframe}..."):
            manual_connect(
                source,
                symbol,
                api_key,
                bars=bars,
                timeframe=timeframe,
            )

        st.success(f"Connected {source.upper()} {symbol} {timeframe}.")
        st.rerun()

    except Exception as exc:
        st.error(f"{source.upper()} connection failed: {exc}")


# ==========================================================
# SAFE SIMILARITY ENGINE WRAPPER
# ==========================================================

def _fallback_similarity_engine(df, horizon=120, lookback_days=100, window=120, step=10, max_rank=25):
    summary = {
        "Status": "Backtest similarity engine unavailable.",
        "Dominant Similar Bias": "WAIT",
        "Bullish Similar %": 0.0,
        "Bearish Similar %": 0.0,
        "Sideways Similar %": 100.0,
        "Safe Similarity Score /10": 0.0,
        "Top Similarity %": 0.0,
        "Days Ranked": 0,
        "Windows Scanned": 0,
        "Search Rule": "Fallback mode. Import tabs.backtest.advanced_last120_similarity_engine to enable full matching.",
    }

    return pd.DataFrame(), summary


def _safe_similarity_engine(df, horizon=120, lookback_days=100, window=120, step=10, max_rank=25):
    engine = _backtest_similarity_engine

    if engine is None:
        return _fallback_similarity_engine(
            df,
            horizon=horizon,
            lookback_days=lookback_days,
            window=window,
            step=step,
            max_rank=max_rank,
        )

    try:
        sim_df, summary = engine(
            df,
            horizon=horizon,
            lookback_days=lookback_days,
            window=window,
            step=step,
            max_rank=max_rank,
        )

        if summary is None:
            summary = {}

        if sim_df is None:
            sim_df = pd.DataFrame()

        summary.setdefault("Status", "OK" if not sim_df.empty else "Need more data.")
        summary.setdefault("Dominant Similar Bias", "WAIT")
        summary.setdefault("Bullish Similar %", 0.0)
        summary.setdefault("Bearish Similar %", 0.0)
        summary.setdefault("Sideways Similar %", 0.0)
        summary.setdefault("Safe Similarity Score /10", 0.0)
        summary.setdefault("Top Similarity %", 0.0)
        summary.setdefault("Search Rule", "Uses older data only; excludes today and yesterday when timestamps exist.")

        return sim_df, summary

    except Exception as exc:
        summary = {
            "Status": f"Similarity engine crashed: {exc}",
            "Dominant Similar Bias": "WAIT",
            "Bullish Similar %": 0.0,
            "Bearish Similar %": 0.0,
            "Sideways Similar %": 100.0,
            "Safe Similarity Score /10": 0.0,
            "Top Similarity %": 0.0,
            "Days Ranked": 0,
            "Windows Scanned": 0,
            "Search Rule": "Similarity engine failed safely.",
        }

        return pd.DataFrame(), summary


# ==========================================================
# CHART
# ==========================================================

def _show_candlestick_chart(dfi):
    if dfi is None or dfi.empty:
        st.info("No chart data available.")
        return

    needed = ["time", "open", "high", "low", "close"]

    missing = [c for c in needed if c not in dfi.columns]

    if missing:
        st.warning(f"Chart missing columns: {missing}")
        return

    chart_df = dfi.tail(180).copy()

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=chart_df["time"],
                open=chart_df["open"],
                high=chart_df["high"],
                low=chart_df["low"],
                close=chart_df["close"],
                name="Price",
            )
        ]
    )

    fig.update_layout(
        height=390,
        xaxis_rangeslider_visible=False,
        margin=dict(l=5, r=5, t=10, b=5),
    )

    st.plotly_chart(fig, use_container_width=True)


# ==========================================================
# SNAPSHOT SAVE CONTROL
# ==========================================================

def _save_engine_snapshot_once(q, symbol):
    """
    Prevent saving duplicate rows on every Streamlit rerun.
    Saves at most once every 60 seconds unless user presses manual save.
    """
    now = pd.Timestamp.now()
    last_save = _safe_session_get("engine_last_auto_save_time")

    should_save = False

    if last_save is None:
        should_save = True
    else:
        try:
            elapsed = (now - pd.to_datetime(last_save)).total_seconds()
            should_save = elapsed >= 60
        except Exception:
            should_save = True

    if should_save:
        row = {
            "time": now,
            "symbol": symbol,
            **q,
        }

        ok, msg = _safe_append_csv("engine_mix_snapshots", row)

        if ok:
            st.session_state.engine_last_auto_save_time = now

        return ok, msg

    return True, "Skipped duplicate auto-save."


# ==========================================================
# MAIN STREAMLIT TAB
# ==========================================================

def show():
    st.markdown("# ⚡ Engine — One Efficient Decision Dashboard")

    st.caption(
        "Main thresholds show Good / Bad / Very Good / Dangerous under each important engine value. "
        "This version is safer against missing data, failed imports, failed MT5/Twelve connections, and rerun duplicate saves."
    )

    engine_symbol = st.text_input(
        "Symbol",
        value=_safe_session_get("symbol", "XAUUSD"),
        key="engine_symbol",
    )

    engine_symbol = str(engine_symbol or "XAUUSD").upper().strip()
    st.session_state.symbol = engine_symbol

    api_key = _safe_session_get("twelve_api_key", "")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Connect MT5 M1", use_container_width=True, key="engine_mt5"):
            _safe_manual_connect("mt5", st.session_state.symbol, api_key, bars=5000, timeframe="M1")

    with c2:
        if st.button("Connect MT5 M2", use_container_width=True, key="engine_mt5_m2"):
            _safe_manual_connect("mt5", st.session_state.symbol, api_key, bars=80000, timeframe="M2")

    with c3:
        if st.button("Connect Twelve", use_container_width=True, key="engine_twelve"):
            _safe_manual_connect("twelve", st.session_state.symbol, api_key, bars=5000, timeframe="M1")

    with c4:
        if st.button("Connect Fallback", use_container_width=True, key="engine_fallback"):
            _safe_manual_connect("fallback", st.session_state.symbol, api_key, bars=5000, timeframe="M1")

    df = _safe_session_get("last_df")

    if df is None:
        st.warning("No live data yet. Click a connect button. Dashboard will not auto-connect.")
        return

    dfi = _safe_add_indicators(df)

    if dfi.empty:
        st.error("Data loaded, but indicators could not be calculated yet.")
        with st.expander("Debug raw data"):
            try:
                st.write(df)
            except Exception:
                st.write("Could not display raw data.")
        return

    q = _safe_quant_stack(df, dfi)

    tabs = st.tabs([
        "🎯 Decision + Thresholds",
        "🧠 Similar Regime",
        "📈 Chart + Compact Data",
        "💾 Save / Debug",
    ])

    # ======================================================
    # TAB 1: DECISION
    # ======================================================

    with tabs[0]:
        row1 = st.columns(5)

        bias = q.get("bias", "WAIT")
        bias_status = "GOOD" if bias in ["BUY", "SELL"] else "BAD"
        bias_note = "Directional output; confirm with thresholds" if bias in ["BUY", "SELL"] else "No strong direction yet"

        _metric_with_status(
            row1[0],
            "Priority Bias",
            bias,
            bias_status,
            bias_note,
        )

        safety_status, safety_note = _status_for_metric("Safety %", q.get("safe_pct", 0))

        _metric_with_status(
            row1[1],
            "Safety /10",
            q.get("scale10", 0),
            safety_status,
            safety_note,
        )

        _metric_with_status(row1[2], "Safety %", q.get("safe_pct", 0))
        _metric_with_status(row1[3], "ADX", q.get("adx", 0))
        _metric_with_status(row1[4], "Pressure", q.get("pressure", 0))

        row2 = st.columns(5)

        _metric_with_status(row2[0], "ML Confidence %", q.get("ml_conf_pct", 0))
        _metric_with_status(row2[1], "History Match %", q.get("history_match_pct", 0))
        _metric_with_status(row2[2], "Mean Revert Risk %", q.get("mean_revert_risk_pct", 0))
        _metric_with_status(row2[3], "Fat Tail Risk %", q.get("fat_tail_risk_pct", 0))
        _metric_with_status(row2[4], "Spoofing Risk %", q.get("spoofing_risk_pct", 0))

        st.markdown("#### Threshold Table")
        st.dataframe(_threshold_table(q), use_container_width=True, hide_index=True)

        auto_save = st.checkbox(
            "Auto-save engine snapshot safely every 60 seconds",
            value=True,
            key="engine_auto_save_snapshot",
        )

        if auto_save:
            _save_engine_snapshot_once(q, st.session_state.symbol)

    # ======================================================
    # TAB 2: SIMILAR REGIME
    # ======================================================

    with tabs[1]:
        st.markdown("### Last-120 Similar Regime, same engine as Backtest")

        sim_controls = st.columns(4)

        with sim_controls[0]:
            sim_lookback = st.slider(
                "Lookback days",
                30,
                120,
                100,
                5,
                key="engine_sim_lookback",
            )

        with sim_controls[1]:
            sim_window = st.number_input(
                "Window candles",
                min_value=60,
                max_value=240,
                value=120,
                step=10,
                key="engine_sim_window",
            )

        with sim_controls[2]:
            sim_horizon = st.number_input(
                "Future context candles",
                min_value=30,
                max_value=240,
                value=120,
                step=10,
                key="engine_sim_horizon",
            )

        with sim_controls[3]:
            sim_step = st.select_slider(
                "Scan step",
                options=[2, 4, 6, 10, 15, 20],
                value=10,
                key="engine_sim_step",
            )

        run_sim = st.button(
            "Run Similar Regime Scan",
            use_container_width=True,
            key="engine_run_similarity",
        )

        if run_sim or "engine_last_similarity_result" not in st.session_state:
            sim_df, summary = _safe_similarity_engine(
                dfi,
                horizon=int(sim_horizon),
                lookback_days=int(sim_lookback),
                window=int(sim_window),
                step=int(sim_step),
                max_rank=25,
            )

            st.session_state.engine_last_similarity_result = {
                "sim_df": sim_df,
                "summary": summary,
            }

        saved_sim = _safe_session_get("engine_last_similarity_result", {})
        sim_df = saved_sim.get("sim_df", pd.DataFrame())
        summary = saved_sim.get("summary", {})

        cols = st.columns(5)

        for col, key in zip(
            cols,
            [
                "Dominant Similar Bias",
                "Bullish Similar %",
                "Bearish Similar %",
                "Safe Similarity Score /10",
                "Top Similarity %",
            ],
        ):
            col.metric(key, summary.get(key, "N/A"))

        st.caption(summary.get("Search Rule", "Uses older data only; excludes today and yesterday when timestamps exist."))

        if sim_df is None or sim_df.empty:
            st.warning(summary.get("Status", "Need more data for similar-regime matching."))
        else:
            st.dataframe(sim_df, use_container_width=True, height=420)

    # ======================================================
    # TAB 3: CHART + DATA
    # ======================================================

    with tabs[2]:
        _show_candlestick_chart(dfi)

        st.markdown("#### Compact latest data only")

        compact = _compact_latest_data(dfi)

        if compact.empty:
            st.info("No compact data available.")
        else:
            st.dataframe(compact, use_container_width=True, height=380)

    # ======================================================
    # TAB 4: SAVE / DEBUG
    # ======================================================

    with tabs[3]:
        st.markdown("### Save / Debug")

        if st.button("💾 Save Engine Snapshot Now", use_container_width=True, key="engine_save_now"):
            row = {
                "time": pd.Timestamp.now(),
                "symbol": st.session_state.symbol,
                **q,
            }

            ok, msg = _safe_append_csv("engine_mix_snapshots", row)

            if ok:
                st.success("Engine snapshot saved.")
            else:
                st.error(msg)

        st.markdown("#### Current Quant Output")
        st.json(q)

        with st.expander("Latest dataframe columns"):
            st.write(list(dfi.columns))

        with st.expander("Latest 10 rows"):
            st.dataframe(dfi.tail(10), use_container_width=True)

        with st.expander("Import status"):
            st.write({
                "add_indicators_available": add_indicators is not None,
                "quant_stack_available": quant_stack is not None,
                "manual_connect_available": manual_connect is not None,
                "append_csv_available": append_csv is not None,
                "backtest_similarity_engine_available": _backtest_similarity_engine is not None,
            })