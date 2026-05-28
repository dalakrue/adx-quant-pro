import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from core.common import synthetic_ohlc
from core.data_connectors import manual_connect, fetch_mt5, fetch_twelve, resample_ohlc
from core.database import append_csv, read_csv
from core.quant_models import add_indicators, quant_stack

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None


BASE_FEATURES = [
    "adx", "plus_di", "minus_di", "atr", "pressure", "adx_slope",
    "momentum", "volatility", "mean_dist", "vol_decay", "fat_tail",
]


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


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _safe_append_csv(name: str, row: dict):
    try:
        append_csv(name, row)
        return True, "Saved."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def _safe_read_csv(name: str) -> pd.DataFrame:
    try:
        out = read_csv(name)
        if out is None:
            return pd.DataFrame()
        return out
    except Exception:
        return pd.DataFrame()


def _ensure_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make sure dataframe has time/open/high/low/close.
    This prevents the page from crashing when MT5/Twelve/cache gives imperfect data.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    work = df.copy()

    if "time" not in work.columns:
        if isinstance(work.index, pd.DatetimeIndex):
            work = work.reset_index().rename(columns={"index": "time"})
        else:
            work["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(work), freq="2min")

    work["time"] = pd.to_datetime(work["time"], errors="coerce")

    rename_map = {}
    for c in work.columns:
        lc = str(c).lower()
        if lc in ["datetime", "date", "timestamp"]:
            rename_map[c] = "time"
        elif lc == "o":
            rename_map[c] = "open"
        elif lc == "h":
            rename_map[c] = "high"
        elif lc == "l":
            rename_map[c] = "low"
        elif lc == "c":
            rename_map[c] = "close"

    if rename_map:
        work = work.rename(columns=rename_map)

    required = ["open", "high", "low", "close"]

    if "close" not in work.columns:
        return pd.DataFrame()

    work["close"] = pd.to_numeric(work["close"], errors="coerce").ffill().bfill()

    if "open" not in work.columns:
        work["open"] = work["close"].shift(1).fillna(work["close"])

    if "high" not in work.columns:
        work["high"] = work[["open", "close"]].max(axis=1)

    if "low" not in work.columns:
        work["low"] = work[["open", "close"]].min(axis=1)

    for col in required:
        work[col] = pd.to_numeric(work[col], errors="coerce").ffill().bfill()

    work = work.dropna(subset=["time", "open", "high", "low", "close"]).reset_index(drop=True)

    return work


def _safe_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Indicator-ready OHLC frame with safe numeric columns.
    """
    work = _ensure_ohlc(df)

    if work.empty:
        return pd.DataFrame()

    try:
        work = add_indicators(work)
    except Exception:
        # If indicator engine fails, keep OHLC and create empty feature columns.
        pass

    if work.empty:
        return pd.DataFrame()

    work = work.replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(0).reset_index(drop=True)

    if "time" in work.columns:
        work["time"] = pd.to_datetime(work["time"], errors="coerce")
    else:
        work["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(work), freq="2min")

    for col in ["open", "high", "low", "close"]:
        if col not in work.columns:
            return pd.DataFrame()
        work[col] = pd.to_numeric(work[col], errors="coerce").ffill().bfill()

    for col in BASE_FEATURES:
        if col not in work.columns:
            work[col] = 0.0
        work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0.0)

    work = work.dropna(subset=["time", "open", "high", "low", "close"]).reset_index(drop=True)

    return work


def _series(window_df: pd.DataFrame, col: str, default=0.0) -> np.ndarray:
    if col in window_df.columns:
        return pd.to_numeric(window_df[col], errors="coerce").ffill().bfill().fillna(default).to_numpy(dtype=float)

    return np.full(len(window_df), float(default), dtype=float)


def _zscore(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    mean = float(np.nanmean(a)) if len(a) else 0.0
    std = float(np.nanstd(a)) if len(a) else 0.0

    if not np.isfinite(std) or std < 1e-12:
        return np.nan_to_num(a - mean, nan=0.0, posinf=0.0, neginf=0.0)

    return np.nan_to_num((a - mean) / std, nan=0.0, posinf=0.0, neginf=0.0)


# ==========================================================
# ADVANCED SIMILARITY ENGINE
# ==========================================================

def _window_vector(window_df: pd.DataFrame) -> np.ndarray:
    """
    Vector representing one 120-candle region.

    It compares:
    - close path
    - returns
    - candle range
    - candle body
    - ADX
    - pressure
    - ATR
    - volatility
    - mean distance
    """
    close = _series(window_df, "close")
    open_ = _series(window_df, "open")
    high = _series(window_df, "high")
    low = _series(window_df, "low")

    base = max(abs(float(close[0])), 1e-9)

    close_path = (close / base - 1.0) * 10000.0
    ret = np.r_[0.0, np.diff(close) / np.maximum(np.abs(close[:-1]), 1e-9) * 10000.0]
    candle_range = (high - low) / np.maximum(np.abs(close), 1e-9) * 10000.0
    body = (close - open_) / np.maximum(np.abs(close), 1e-9) * 10000.0

    adx = _series(window_df, "adx") / 50.0
    pressure = _series(window_df, "pressure") / 50.0

    atr = _series(window_df, "atr")
    atr_pct = atr / np.maximum(np.abs(close), 1e-9) * 10000.0

    vol = _series(window_df, "volatility") * 10000.0

    mean_dist = _series(window_df, "mean_dist")
    atr_median = float(np.nanmedian(atr))
    if not np.isfinite(atr_median) or atr_median <= 0:
        atr_median = 1.0
    mean_dist = mean_dist / max(atr_median, 1e-9)

    path = np.concatenate([
        _zscore(close_path),
        _zscore(ret),
        _zscore(candle_range),
        _zscore(body),
        _zscore(adx),
        _zscore(pressure),
        _zscore(atr_pct),
        _zscore(vol),
        _zscore(mean_dist),
    ])

    stats = []
    for arr in [close_path, ret, candle_range, body, adx, pressure, atr_pct, vol, mean_dist]:
        arr = np.asarray(arr, dtype=float)
        stats.extend([
            float(np.nanmean(arr)),
            float(np.nanstd(arr)),
            float(arr[-1] - arr[0]),
            float(np.nanpercentile(arr, 75) - np.nanpercentile(arr, 25)),
            float(np.nanmax(arr) - np.nanmin(arr)),
        ])

    vec = np.concatenate([path, np.asarray(stats, dtype=float)])
    return np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)


def _cosine_similarity_one_to_many(current_vec: np.ndarray, candidate_vecs: list[np.ndarray]) -> np.ndarray:
    if not candidate_vecs:
        return np.array([], dtype=float)

    matrix = np.vstack(candidate_vecs).astype(float)
    current = current_vec.astype(float)

    combined = np.vstack([current.reshape(1, -1), matrix])

    mean = np.nanmean(combined, axis=0)
    std = np.nanstd(combined, axis=0)
    std[~np.isfinite(std) | (std < 1e-12)] = 1.0

    combined = np.nan_to_num((combined - mean) / std, nan=0.0, posinf=0.0, neginf=0.0)

    current_n = combined[0]
    matrix_n = combined[1:]

    denom = np.linalg.norm(matrix_n, axis=1) * max(float(np.linalg.norm(current_n)), 1e-9)
    sims = (matrix_n @ current_n) / np.maximum(denom, 1e-9)

    return np.clip(sims, -1.0, 1.0)


def _label_from_move(move_pct: float) -> str:
    move_pct = _safe_float(move_pct)

    if move_pct > 0.04:
        return "BULLISH"

    if move_pct < -0.04:
        return "BEARISH"

    return "SIDEWAYS"


def _quality_from_similarity(similarity_pct: float) -> str:
    similarity_pct = _safe_float(similarity_pct)

    if similarity_pct >= 88:
        return "VERY GOOD MATCH"

    if similarity_pct >= 78:
        return "GOOD MATCH"

    if similarity_pct >= 68:
        return "OK / USE CARE"

    return "WEAK MATCH"


def _empty_similarity_summary():
    return {
        "Status": "Need more M2 data for last-120 similar-day matching.",
        "Dominant Similar Bias": "WAIT",
        "Bullish Similar %": 0.0,
        "Bearish Similar %": 0.0,
        "Sideways Similar %": 0.0,
        "Safe Similarity Score /10": 0.0,
        "Top Similarity %": 0.0,
        "Days Ranked": 0,
        "Windows Scanned": 0,
        "Data Mode": "M2 last-120 similar-day finder",
    }


def advanced_last120_similarity_engine(
    df: pd.DataFrame,
    horizon: int = 120,
    lookback_days: int = 100,
    window: int = 120,
    step: int = 6,
    max_rank: int = 40,
):
    """
    Find older days whose 120-candle M2 regime is most similar to the latest 120 candles.

    Important:
    - compares latest 120 candles to older rolling 120-candle regions;
    - scans last N days;
    - excludes today and yesterday when timestamps exist;
    - ranks best matching region per day;
    - next_120_context is only historical context, not a direct signal.
    """
    summary = _empty_similarity_summary()

    try:
        work = _safe_feature_frame(df)

        horizon = int(max(1, horizon))
        window = int(max(30, window))
        step = int(max(1, step))
        max_rank = int(max(5, max_rank))
        lookback_days = int(max(5, lookback_days))

        min_need = max(window + horizon + 30, 300)

        if work.empty or len(work) < min_need:
            summary["Status"] = f"Need more candles. Have {len(work)}, need at least {min_need}."
            return pd.DataFrame(), summary

        latest_time = pd.to_datetime(work["time"].iloc[-1], errors="coerce")
        latest_day = latest_time.date() if pd.notna(latest_time) else None
        yesterday = (latest_time - pd.Timedelta(days=1)).date() if pd.notna(latest_time) else None
        earliest = latest_time - pd.Timedelta(days=lookback_days) if pd.notna(latest_time) else pd.NaT

        current = work.tail(window).copy()
        current_vec = _window_vector(current)

        rows = []
        vecs = []

        max_start_for_future = len(work) - window - horizon

        if max_start_for_future <= 0:
            summary["Status"] = "Not enough candles after historical windows for future context."
            return pd.DataFrame(), summary

        for start in range(0, max_start_for_future + 1, step):
            end = start + window

            candidate_end_time = pd.to_datetime(work["time"].iloc[end - 1], errors="coerce")

            if pd.notna(latest_time) and pd.notna(candidate_end_time):
                cday = candidate_end_time.date()

                if cday in {latest_day, yesterday}:
                    continue

                if candidate_end_time >= latest_time:
                    continue

                if pd.notna(earliest) and candidate_end_time < earliest:
                    continue
            else:
                cday = str(end)

            candidate = work.iloc[start:end]

            vecs.append(_window_vector(candidate))

            end_close = _safe_float(work["close"].iloc[end - 1])
            future_close = _safe_float(work["close"].iloc[end + horizon - 1])

            future_move = future_close - end_close
            future_move_pct = future_move / max(abs(end_close), 1e-9) * 100.0

            rows.append({
                "match_day": cday,
                "matched_region_end": candidate_end_time,
                "region_start_time": pd.to_datetime(work["time"].iloc[start], errors="coerce"),
                "start_index": start,
                "end_index": end - 1,
                "close_at_region_end": end_close,
                "next_120_m2_close": future_close,
                "next_120_m2_move": future_move,
                "next_120_m2_move_pct": future_move_pct,
                "next_120_context": _label_from_move(future_move_pct),
                "adx": _safe_float(work["adx"].iloc[end - 1]) if "adx" in work.columns else 0.0,
                "pressure": _safe_float(work["pressure"].iloc[end - 1]) if "pressure" in work.columns else 0.0,
                "atr": _safe_float(work["atr"].iloc[end - 1]) if "atr" in work.columns else 0.0,
                "volatility": _safe_float(work["volatility"].iloc[end - 1]) if "volatility" in work.columns else 0.0,
            })

        if not rows:
            summary["Status"] = "No older M2 windows found after excluding today and yesterday. Connect more history."
            return pd.DataFrame(), summary

        sims = _cosine_similarity_one_to_many(current_vec, vecs)

        out = pd.DataFrame(rows)
        out["similarity_pct"] = np.clip((sims + 1.0) / 2.0 * 100.0, 0, 100)
        out["match_quality"] = out["similarity_pct"].apply(_quality_from_similarity)

        out = (
            out.sort_values("similarity_pct", ascending=False)
            .drop_duplicates("match_day", keep="first")
            .sort_values("similarity_pct", ascending=False)
            .head(max_rank)
            .reset_index(drop=True)
        )

        if out.empty:
            summary["Status"] = "No eligible days after duplicate-day filtering."
            return pd.DataFrame(), summary

        out.insert(0, "rank", np.arange(1, len(out) + 1))

        weights = out["similarity_pct"].clip(lower=0) / 100.0
        total_w = max(float(weights.sum()), 1e-9)

        bull = float(weights[out["next_120_context"] == "BULLISH"].sum() / total_w * 100.0)
        bear = float(weights[out["next_120_context"] == "BEARISH"].sum() / total_w * 100.0)
        side = max(0.0, 100.0 - bull - bear)

        if bull > bear and bull > side:
            dominant = "BUY / BULLISH"
        elif bear > bull and bear > side:
            dominant = "SELL / BEARISH"
        else:
            dominant = "WAIT / SIDEWAYS"

        top_similarity = float(out["similarity_pct"].iloc[0])
        conviction = max(bull, bear, side) - sorted([bull, bear, side])[-2]
        safe_score = float(np.clip((top_similarity * 0.60 + conviction * 0.40) / 10.0, 0, 10))

        summary.update({
            "Status": "OK",
            "Dominant Similar Bias": dominant,
            "Bullish Similar %": round(bull, 2),
            "Bearish Similar %": round(bear, 2),
            "Sideways Similar %": round(side, 2),
            "Safe Similarity Score /10": round(safe_score, 2),
            "Top Similarity %": round(top_similarity, 2),
            "Days Ranked": int(len(out)),
            "Windows Scanned": int(len(rows)),
            "Latest 120 End": str(latest_time),
            "Search Rule": f"Last {lookback_days} days, excluding today and yesterday, best 120-candle M2 region per day",
        })

        display_cols = [
            "rank",
            "match_day",
            "matched_region_end",
            "similarity_pct",
            "match_quality",
            "next_120_context",
            "next_120_m2_move",
            "next_120_m2_move_pct",
            "adx",
            "pressure",
            "atr",
            "close_at_region_end",
            "next_120_m2_close",
        ]

        for col in [
            "similarity_pct",
            "next_120_m2_move",
            "next_120_m2_move_pct",
            "adx",
            "pressure",
            "atr",
            "close_at_region_end",
            "next_120_m2_close",
        ]:
            if col in out.columns:
                out[col] = pd.to_numeric(out[col], errors="coerce").round(4)

        return out[[c for c in display_cols if c in out.columns]], summary

    except Exception as exc:
        summary["Status"] = f"Similarity engine error: {exc}"
        return pd.DataFrame(), summary


# ==========================================================
# DATA LOADING
# ==========================================================

def _bars_for_days(timeframe: str, days: int) -> int:
    tf = str(timeframe).upper()

    if tf == "M1":
        per_day = 1440
    elif tf == "M2":
        per_day = 720
    elif tf == "M5":
        per_day = 288
    elif tf == "M15":
        per_day = 96
    elif tf == "M30":
        per_day = 48
    elif tf == "H1":
        per_day = 24
    else:
        per_day = 720

    return int(per_day * (int(days) + 3) + 300)


def _demo_history(symbol: str, timeframe: str, bars: int) -> tuple[pd.DataFrame, str]:
    try:
        demo = synthetic_ohlc(symbol, bars=max(int(bars) * 2, 2000))

        if str(timeframe).upper() == "M2":
            try:
                demo = resample_ohlc(demo, "M2")
            except Exception:
                pass

        return demo, "SAFE_DEMO: generated local synthetic data"
    except Exception as exc:
        return pd.DataFrame(), f"SAFE_DEMO failed: {exc}"


def _fetch_twelve_safe(symbol: str, api_key: str, timeframe: str, bars: int) -> tuple[pd.DataFrame, bool, str]:
    try:
        timeframe = str(timeframe).upper()

        if timeframe == "M2":
            raw, ok, msg = fetch_twelve(symbol, api_key=api_key, interval="1min", bars=bars * 2)

            if ok:
                try:
                    df = resample_ohlc(raw, "M2")
                    return df, True, f"{msg} → resampled to M2"
                except Exception as exc:
                    return raw, True, f"{msg} but M2 resample failed: {exc}"

            return raw, False, msg

        interval = {
            "M1": "1min",
            "M5": "5min",
            "M15": "15min",
            "M30": "30min",
            "H1": "1h",
        }.get(timeframe, "1min")

        df, ok, msg = fetch_twelve(symbol, api_key=api_key, interval=interval, bars=bars)
        return df, ok, msg

    except Exception as exc:
        return pd.DataFrame(), False, f"Twelve fetch crashed: {exc}"


def _fetch_mt5_safe(symbol: str, timeframe: str, bars: int) -> tuple[pd.DataFrame, bool, str]:
    try:
        df, ok, msg = fetch_mt5(symbol, timeframe=timeframe, bars=bars)
        return df, ok, msg
    except Exception as exc:
        return pd.DataFrame(), False, f"MT5 fetch crashed: {exc}"


def _load_symbol_history(
    symbol: str,
    mode: str,
    api_key: str,
    timeframe: str,
    lookback_days: int,
) -> tuple[pd.DataFrame, str]:
    bars = _bars_for_days(timeframe, lookback_days)

    symbol = str(symbol).strip().upper() or "XAUUSD"
    mode = str(mode).lower().strip()
    timeframe = str(timeframe).upper()

    if mode in ["demo", "demo/cache", "safe_demo"]:
        return _demo_history(symbol, timeframe, bars)

    if mode == "mt5":
        df, ok, msg = _fetch_mt5_safe(symbol, timeframe, bars)

        if ok and df is not None and len(df) >= 300:
            return df, f"MT5: {msg}"

        demo, demo_msg = _demo_history(symbol, timeframe, bars)
        return demo, f"{demo_msg} because MT5 failed: {msg}"

    if mode == "twelve":
        df, ok, msg = _fetch_twelve_safe(symbol, api_key, timeframe, bars)

        if ok and df is not None and len(df) >= 300:
            return df, f"TWELVE: {msg}"

        demo, demo_msg = _demo_history(symbol, timeframe, bars)
        return demo, f"{demo_msg} because Twelve failed: {msg}"

    # fallback mode: try MT5 first, then Twelve, then safe demo
    df, ok, msg = _fetch_mt5_safe(symbol, timeframe, bars)

    if ok and df is not None and len(df) >= 300:
        return df, f"MT5: {msg}"

    mt5_msg = msg

    df, ok, msg = _fetch_twelve_safe(symbol, api_key, timeframe, bars)

    if ok and df is not None and len(df) >= 300:
        return df, f"TWELVE after MT5 failed: {msg}"

    demo, demo_msg = _demo_history(symbol, timeframe, bars)
    return demo, f"{demo_msg}. MT5 failed: {mt5_msg}. Twelve failed: {msg}"


# ==========================================================
# UI HELPERS
# ==========================================================

def _summary_card(summary: dict):
    cols = st.columns(6)

    keys = [
        "Dominant Similar Bias",
        "Safe Similarity Score /10",
        "Top Similarity %",
        "Bullish Similar %",
        "Bearish Similar %",
        "Days Ranked",
    ]

    for col, key in zip(cols, keys):
        col.metric(key, summary.get(key, "N/A"))

    st.caption(summary.get("Search Rule", "M2 similar-day scan: latest 120 candles vs older 120-candle regions."))


def _plot_latest_chart(work: pd.DataFrame):
    if work is None or work.empty:
        return

    needed = ["time", "open", "high", "low", "close"]
    if any(c not in work.columns for c in needed):
        st.warning("Chart needs time/open/high/low/close columns.")
        return

    chart_df = work.tail(240).copy()

    fig = go.Figure(data=[
        go.Candlestick(
            x=chart_df["time"],
            open=chart_df["open"],
            high=chart_df["high"],
            low=chart_df["low"],
            close=chart_df["close"],
            name="Latest 240 M2 candles",
        )
    ])

    fig.update_layout(
        height=430,
        xaxis_rangeslider_visible=False,
        margin=dict(l=5, r=5, t=10, b=5),
    )

    st.plotly_chart(fig, use_container_width=True)


def _show_status_box(summaries: list[dict]):
    if not summaries:
        return

    bad = [s for s in summaries if str(s.get("Status", "")).upper() != "OK"]

    if bad:
        with st.expander("Warnings / data messages", expanded=False):
            for s in bad:
                st.warning(f"{s.get('Symbol', 'N/A')}: {s.get('Status', 'Unknown status')}")


def _clean_symbols(symbols_text: str):
    symbols = [s.strip().upper() for s in str(symbols_text).split(",") if s.strip()]
    if not symbols:
        symbols = [st.session_state.get("symbol", "XAUUSD")]
    return symbols[:6]


# ==========================================================
# MAIN STREAMLIT PAGE
# ==========================================================

def show():
    st.markdown("# 🧠 Fast M2 Similar-Day Finder")

    st.caption(
        "Compares the latest 120 M2 candles with older 120-candle M2 regions, "
        "excludes today/yesterday, and ranks similar days. This is market-regime matching, not a full strategy backtest."
    )

    st_autorefresh(interval=600000, key="backtest_m2_similarity_refresh")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        symbols_text = st.text_input(
            "Symbols / various data",
            value=st.session_state.get("bt_symbols", st.session_state.get("symbol", "XAUUSD")),
            help="Use comma-separated symbols, for example: XAUUSD,EURUSD,GBPUSD",
            key="bt_symbols",
        )

    with c2:
        source_mode = st.selectbox(
            "Data source",
            ["fallback", "mt5", "twelve", "demo/cache"],
            index=0,
            key="bt_source_mode",
        )

    with c3:
        lookback_days = st.slider(
            "Search last N days",
            30,
            120,
            100,
            5,
            key="bt_lookback_100",
        )

    with c4:
        scan_step = st.select_slider(
            "Scan speed",
            options=[2, 4, 6, 10, 15, 20],
            value=6,
            key="bt_scan_step",
            help="Lower = more precise/slower. 6 scans every 12 minutes on M2.",
        )

    d1, d2, d3 = st.columns(3)

    with d1:
        window = st.number_input(
            "Current region candles",
            min_value=60,
            max_value=240,
            value=120,
            step=10,
            key="bt_window_120",
        )

    with d2:
        future_context = st.number_input(
            "Context after match",
            min_value=30,
            max_value=240,
            value=120,
            step=10,
            key="bt_future_120",
        )

    with d3:
        max_rank = st.number_input(
            "Rank top days",
            min_value=10,
            max_value=80,
            value=40,
            step=5,
            key="bt_max_rank",
        )

    run = st.button(
        "🔎 Find Similar Days Now",
        use_container_width=True,
        type="primary",
        key="bt_run_similarity",
    )

    symbols = _clean_symbols(symbols_text)
    api_key = st.session_state.get("twelve_api_key", "")

    if run or "bt_last_similarity" not in st.session_state:
        all_rows = []
        summaries = []
        first_work = None

        progress = st.progress(0)
        status = st.empty()

        for i, sym in enumerate(symbols):
            status.info(f"Loading and scanning {sym}...")

            df, msg = _load_symbol_history(
                sym,
                source_mode,
                api_key,
                "M2",
                int(lookback_days),
            )

            work = _safe_feature_frame(df)

            if first_work is None and work is not None and not work.empty:
                first_work = work

            sim_df, summary = advanced_last120_similarity_engine(
                work,
                horizon=int(future_context),
                lookback_days=int(lookback_days),
                window=int(window),
                step=int(scan_step),
                max_rank=int(max_rank),
            )

            summary["Symbol"] = sym
            summary["Source Message"] = msg
            summaries.append(summary)

            if sim_df is not None and not sim_df.empty:
                sim_df.insert(1, "symbol", sym)
                all_rows.append(sim_df)

            progress.progress((i + 1) / max(len(symbols), 1))

        status.empty()
        progress.empty()

        combined = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()

        if not combined.empty:
            combined = combined.sort_values(["similarity_pct", "rank"], ascending=[False, True]).reset_index(drop=True)
            combined.insert(0, "global_rank", np.arange(1, len(combined) + 1))

        st.session_state.bt_last_similarity = {
            "combined": combined,
            "summaries": summaries,
            "work": first_work,
        }

    saved = st.session_state.get("bt_last_similarity", {})
    combined = saved.get("combined", pd.DataFrame())
    summaries = saved.get("summaries", [])
    work = saved.get("work", None)

    if summaries:
        sum_df = pd.DataFrame(summaries)
        primary = summaries[0]

        _summary_card(primary)
        _show_status_box(summaries)

        with st.expander("Per-symbol summary", expanded=len(summaries) > 1):
            show_cols = [
                c for c in [
                    "Symbol",
                    "Status",
                    "Dominant Similar Bias",
                    "Top Similarity %",
                    "Days Ranked",
                    "Windows Scanned",
                    "Source Message",
                ]
                if c in sum_df.columns
            ]
            st.dataframe(sum_df[show_cols], use_container_width=True)

    tabs = st.tabs([
        "🏆 Similar Day Ranking",
        "📈 Latest M2 Chart",
        "💾 Save / History",
        "ℹ️ How to read",
    ])

    with tabs[0]:
        if combined is None or combined.empty:
            st.warning("No similar-day ranking yet. Click Find Similar Days Now, or connect more MT5 M2 history.")
        else:
            st.dataframe(combined, use_container_width=True, height=520)

            best = combined.iloc[0].to_dict()

            st.success(
                f"Best match: {best.get('symbol')} on {best.get('match_day')} | "
                f"similarity {best.get('similarity_pct')}% | "
                f"context after next 120 M2: {best.get('next_120_context')}"
            )

            with st.expander("Best match detail"):
                st.json(best)

    with tabs[1]:
        if work is not None and not work.empty:
            _plot_latest_chart(work)

            latest_cols = [
                "time",
                "open",
                "high",
                "low",
                "close",
                "adx",
                "pressure",
                "atr",
                "volatility",
                "mean_dist",
            ]

            show_cols = [c for c in latest_cols if c in work.columns]
            st.dataframe(work[show_cols].tail(120), use_container_width=True)
        else:
            st.info("Chart appears after data is loaded.")

    with tabs[2]:
        if st.button("💾 Save current similar-day result", use_container_width=True, key="bt_save_similarity"):
            if combined is None or combined.empty:
                st.warning("Nothing to save yet.")
            else:
                top = combined.iloc[0].to_dict()

                save_row = {
                    "saved_time": str(pd.Timestamp.now()),
                    **top,
                }

                ok, msg = _safe_append_csv("similar_day_results", save_row)

                if ok:
                    st.success("Saved top similar-day result.")
                else:
                    st.error(msg)

        hist = _safe_read_csv("similar_day_results")

        if hist.empty:
            st.info("No saved similar-day results yet.")
        else:
            st.dataframe(hist.tail(200), use_container_width=True)

    with tabs[3]:
        st.markdown(
            """
### How to read this page

**Dominant Similar Bias**  
This is the weighted direction from historical similar regions. It is not a direct entry signal.

**Similarity %**  
Higher means the old 120-candle region looked more similar to the current latest 120 candles.

**next_120_context**  
This shows what happened after that old similar region. Use it as context, not as guaranteed prediction.

**Excluded data**  
Today and yesterday are excluded when timestamps are available.

**Scan speed**  
Lower number = more accurate but slower.  
Higher number = faster but less detailed.

**Data source**
- `fallback`: MT5 first, then Twelve Data, then safe demo.
- `mt5`: MT5 only, then safe demo if MT5 fails.
- `twelve`: Twelve Data only, then safe demo if Twelve fails.
- `demo/cache`: safe demo mode directly.

**Best use**
Use this to adjust your trading plan when the current market structure looks similar to a previous day.
            """
        )