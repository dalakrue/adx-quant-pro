import os
import json
import math
import time
import urllib.parse
import urllib.request
import traceback
from datetime import timedelta

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# CLEAN INDEPENDENT PRE TAB
# Keeps:
#   1) Advanced History Match
#   2) Pre-Trade Check
#   3) Exit Survivability
#
# Removed:
#   - Combined 4H Bias tab
#   - Main Decision tab
#
# History Match purpose:
#   - NOT strategy backtest
#   - Finds similar historical days to today/latest pattern
#   - Top ranked days are non-duplicate
# =========================================================


DATA_KEY = "pre_clean_history_df"
SOURCE_KEY = "pre_clean_history_source"
SYMBOL_KEY = "pre_clean_history_symbol"
TF_KEY = "pre_clean_history_tf"
RESULT_KEY = "pre_clean_history_result"
SUMMARY_KEY = "pre_clean_history_summary"


# =========================================================
# BASIC HELPERS
# =========================================================
def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def safe_num(x, default=0.0):
    try:
        if x is None:
            return float(default)
        if isinstance(x, str) and x.strip() == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def get_secret_or_env(*names, default=""):
    for name in names:
        try:
            v = st.secrets.get(name, None)
            if v:
                return str(v)
        except Exception:
            pass

        try:
            v = os.getenv(name)
            if v:
                return str(v)
        except Exception:
            pass

    return default
# =========================================================
# FULL WORKING TIMER — NO EXTRA PACKAGE NEEDED
# =========================================================
import streamlit.components.v1 as components

TIMER_END_KEY = "trade_end_time"
TIMER_RUNNING_KEY = "trade_timer_running"
TIMER_MINUTES_KEY = "trade_timer_minutes"


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def format_timer(seconds):
    try:
        seconds = int(max(0, seconds))
    except Exception:
        seconds = 0

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02d}:{m:02d}:{s:02d}"


def remaining_seconds():
    end_time = st.session_state.get(TIMER_END_KEY)

    if end_time is None:
        return 0

    try:
        return int(max(0, float(end_time) - time.time()))
    except Exception:
        return 0


def start_trade_timer(minutes):
    minutes = int(max(1, minutes))
    st.session_state[TIMER_MINUTES_KEY] = minutes
    st.session_state[TIMER_END_KEY] = time.time() + minutes * 60
    st.session_state[TIMER_RUNNING_KEY] = True


def reset_trade_timer():
    st.session_state.pop(TIMER_END_KEY, None)
    st.session_state[TIMER_RUNNING_KEY] = False


def timer_panel():
    st.markdown("## ⏳ Trade Countdown Timer")

    if TIMER_MINUTES_KEY not in st.session_state:
        st.session_state[TIMER_MINUTES_KEY] = 240

    c1, c2, c3 = st.columns(3)

    with c1:
        minutes = st.number_input(
            "Timer Minutes",
            min_value=1,
            max_value=1440,
            value=int(st.session_state.get(TIMER_MINUTES_KEY, 240)),
            step=5,
            key="trade_timer_minutes_input_fixed",
        )

    with c2:
        if st.button(
            "▶️ Start Timer",
            type="primary",
            use_container_width=True,
            key="start_trade_timer_fixed",
        ):
            start_trade_timer(minutes)
            safe_rerun()

    with c3:
        if st.button(
            "🔄 Reset Timer",
            use_container_width=True,
            key="reset_trade_timer_fixed",
        ):
            reset_trade_timer()
            safe_rerun()

    remaining = remaining_seconds()

    if remaining <= 0 and st.session_state.get(TIMER_RUNNING_KEY, False):
        st.session_state[TIMER_RUNNING_KEY] = False

    running = bool(st.session_state.get(TIMER_RUNNING_KEY, False))
    end_time = float(st.session_state.get(TIMER_END_KEY, 0) or 0)
    end_ms = int(end_time * 1000)

    if not running or end_ms <= 0:
        st.info("Timer is not running. Set minutes and click Start Timer.")
        display_seconds = 0
        end_ms = 0
    else:
        display_seconds = remaining

    components.html(
        f"""
        <div style="
            padding:16px;
            border-radius:16px;
            background:linear-gradient(135deg,#EFF6FF,#F8FAFC);
            border:1px solid #DCE7F7;
            margin:12px 0;
            text-align:center;
            box-shadow:0 8px 22px rgba(15,23,42,0.08);
            font-family:Arial, sans-serif;
        ">
            <div style="font-size:15px;font-weight:700;color:#111827;">
                ⏳ Trade Countdown
            </div>

            <div id="trade_countdown_value" style="
                font-size:38px;
                font-weight:900;
                color:#1D4ED8;
                margin-top:6px;
            ">
                {format_timer(display_seconds)}
            </div>

            <div id="trade_countdown_status" style="
                font-size:14px;
                font-weight:700;
                margin-top:8px;
                color:#475569;
            ">
                {"✅ Timer running" if running else "Timer stopped"}
            </div>
        </div>

        <script>
        const endTs = {end_ms};
        const running = {str(running).lower()};

        function pad(n) {{
            return String(n).padStart(2, "0");
        }}

        function fmt(seconds) {{
            seconds = Math.max(0, Math.floor(seconds));
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return pad(h) + ":" + pad(m) + ":" + pad(s);
        }}

        function updateTimer() {{
            const value = document.getElementById("trade_countdown_value");
            const status = document.getElementById("trade_countdown_status");

            if (!running || endTs <= 0) {{
                value.innerText = "00:00:00";
                status.innerText = "Timer stopped";
                status.style.color = "#475569";
                return;
            }}

            let left = Math.floor((endTs - Date.now()) / 1000);
            left = Math.max(0, left);

            value.innerText = fmt(left);

            if (left <= 0) {{
                status.innerText = "⛔ Timer finished";
                status.style.color = "#DC2626";
                value.style.color = "#DC2626";
            }} else if (left <= 300) {{
                status.innerText = "🚨 FINAL 5 MINUTES";
                status.style.color = "#DC2626";
                value.style.color = "#DC2626";
            }} else if (left <= 1800) {{
                status.innerText = "⚠️ Only 30 minutes left";
                status.style.color = "#D97706";
                value.style.color = "#D97706";
            }} else {{
                status.innerText = "✅ Timer running";
                status.style.color = "#16A34A";
                value.style.color = "#1D4ED8";
            }}
        }}

        updateTimer();
        setInterval(updateTimer, 1000);
        </script>
        """,
        height=150,
    )

# =========================================================
# SYMBOL / TIMEFRAME
# =========================================================
def mt5_symbol(symbol):
    return str(symbol or "XAUUSD").replace("/", "").replace(" ", "").upper()


def twelve_symbol(symbol):
    raw = str(symbol or "XAU/USD").strip().upper()

    mapping = {
        "XAUUSD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD",
        "GBPUSD": "GBP/USD",
        "USDJPY": "USD/JPY",
        "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD",
        "USDCHF": "USD/CHF",
        "NZDUSD": "NZD/USD",
        "BTCUSD": "BTC/USD",
        "ETHUSD": "ETH/USD",
    }

    return mapping.get(raw, raw)


def timeframe_minutes(tf):
    return {
        "M1": 1,
        "M2": 2,
        "M3": 3,
        "M5": 5,
        "M15": 15,
        "M30": 30,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
    }.get(str(tf).upper(), 1)


def twelve_interval(tf):
    return {
        "M1": "1min",
        "M2": "1min",
        "M3": "1min",
        "M5": "5min",
        "M15": "15min",
        "M30": "30min",
        "H1": "1h",
        "H4": "4h",
        "D1": "1day",
    }.get(str(tf).upper(), "1min")


# =========================================================
# DATA NORMALIZE / RESAMPLE
# =========================================================
def normalize_ohlc(df):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume"])

    work = df.copy()
    work.columns = [str(c).strip() for c in work.columns]

    rename = {
        "datetime": "time",
        "date": "time",
        "timestamp": "time",
        "Time": "time",
        "Datetime": "time",
        "Date": "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "tick_volume": "volume",
        "real_volume": "volume",
        "Tick Volume": "volume",
    }

    for old, new in rename.items():
        if old in work.columns and new not in work.columns:
            work = work.rename(columns={old: new})

    work = work.rename(columns={c: c.lower() for c in work.columns})

    if "datetime" in work.columns and "time" not in work.columns:
        work = work.rename(columns={"datetime": "time"})

    if "date" in work.columns and "time" not in work.columns:
        work = work.rename(columns={"date": "time"})

    required = ["time", "open", "high", "low", "close"]
    missing = [c for c in required if c not in work.columns]

    if missing:
        raise ValueError(f"CSV/data missing columns: {missing}. Need time/open/high/low/close.")

    if pd.api.types.is_numeric_dtype(work["time"]):
        max_time = pd.to_numeric(work["time"], errors="coerce").dropna().max()
        unit = "ms" if max_time and max_time > 10_000_000_000 else "s"
        work["time"] = pd.to_datetime(work["time"], unit=unit, errors="coerce")
    else:
        work["time"] = pd.to_datetime(work["time"], errors="coerce")

    for c in ["open", "high", "low", "close", "volume"]:
        if c not in work.columns:
            work[c] = 0
        work[c] = pd.to_numeric(work[c], errors="coerce")

    work = work.dropna(subset=["time", "open", "high", "low", "close"])
    work = work.sort_values("time").drop_duplicates("time").reset_index(drop=True)

    return work[["time", "open", "high", "low", "close", "volume"]].copy()


def resample_m2_m3(df, tf):
    df = normalize_ohlc(df)
    tf = str(tf).upper()

    if df.empty:
        return df

    if tf not in ["M2", "M3"]:
        return df

    rule = "2min" if tf == "M2" else "3min"

    temp = df.set_index("time").sort_index()

    out = pd.DataFrame()
    out["open"] = temp["open"].resample(rule).first()
    out["high"] = temp["high"].resample(rule).max()
    out["low"] = temp["low"].resample(rule).min()
    out["close"] = temp["close"].resample(rule).last()
    out["volume"] = temp["volume"].resample(rule).sum()

    return out.dropna().reset_index()


# =========================================================
# DATA LOADERS
# =========================================================
@st.cache_data(ttl=300, show_spinner=False)
def load_twelve(symbol, tf, bars, api_key):
    api_key = str(api_key or "").strip()

    if not api_key:
        return pd.DataFrame(), "Twelve Data API key is empty."

    symbol = twelve_symbol(symbol)
    tf = str(tf).upper()
    interval = twelve_interval(tf)

    outputsize = int(min(max(int(bars), 1), 5000))

    if tf in ["M2", "M3"]:
        outputsize = int(min(outputsize * 3, 5000))

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": api_key,
        "format": "JSON",
    }

    url = "https://api.twelvedata.com/time_series?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=25) as r:
            raw = r.read().decode("utf-8")

        payload = json.loads(raw)

        if payload.get("status") == "error":
            return pd.DataFrame(), payload.get("message", "Twelve Data returned error.")

        values = payload.get("values", [])

        if not values:
            return pd.DataFrame(), "Twelve Data returned no candle values."

        df = pd.DataFrame(values)
        df = normalize_ohlc(df)
        df = resample_m2_m3(df, tf)

        return df.tail(int(bars)).reset_index(drop=True), ""

    except Exception as exc:
        return pd.DataFrame(), f"Twelve Data failed: {exc}"


@st.cache_data(ttl=300, show_spinner=False)
def load_mt5(symbol, tf, bars):
    try:
        import MetaTrader5 as mt5
    except Exception:
        return pd.DataFrame(), (
            "MetaTrader5 is not installed. Use Twelve Data, CSV Upload, Session last_df, or Demo Data. "
            "For MT5 install: pip install MetaTrader5"
        )

    symbol = mt5_symbol(symbol)
    tf = str(tf).upper()

    try:
        if not mt5.initialize():
            mt5.shutdown()
            if not mt5.initialize():
                return pd.DataFrame(), "MT5 initialize failed. Open MT5 terminal and log in first."

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M2": getattr(mt5, "TIMEFRAME_M2", mt5.TIMEFRAME_M1),
            "M3": getattr(mt5, "TIMEFRAME_M3", mt5.TIMEFRAME_M1),
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }

        if not mt5.symbol_select(symbol, True):
            return pd.DataFrame(), f"MT5 symbol not selectable: {symbol}"

        rates = mt5.copy_rates_from_pos(symbol, tf_map.get(tf, mt5.TIMEFRAME_M1), 0, int(bars))

        if rates is None or len(rates) == 0:
            return pd.DataFrame(), f"MT5 returned no candles for {symbol} {tf}"

        df = normalize_ohlc(pd.DataFrame(rates))

        return df, ""

    except Exception as exc:
        return pd.DataFrame(), f"MT5 failed: {exc}"


def make_demo_data(symbol="XAUUSD", tf="M2", days=140, seed=10):
    rng = np.random.default_rng(seed)
    tf_min = timeframe_minutes(tf)

    if str(tf).upper() == "D1":
        periods = int(days)
        freq = "1D"
    else:
        periods = int(days * 24 * 60 / max(1, tf_min))
        freq = f"{max(1, tf_min)}min"

    periods = max(periods, 2000)

    end = pd.Timestamp.now().floor("min")
    times = pd.date_range(end=end, periods=periods, freq=freq)

    base = 2300 if "XAU" in str(symbol).upper() else 1.1000

    slow_regime = np.sin(np.linspace(0, 20 * np.pi, periods)) * 0.00045
    vol_regime = 0.00045 + 0.00075 * (np.sin(np.linspace(0, 8 * np.pi, periods)) > 0)
    noise = rng.standard_t(df=4, size=periods) * vol_regime
    rets = slow_regime + noise

    close = base * np.exp(np.cumsum(rets))
    open_ = np.r_[close[0], close[:-1]]

    spread = np.abs(rng.normal(0, 0.0007, periods)) * close
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    volume = rng.integers(50, 2500, periods)

    wick_idx = rng.choice(np.arange(50, periods), size=max(5, periods // 250), replace=False)
    high[wick_idx] += spread[wick_idx] * rng.uniform(2, 5, len(wick_idx))
    low[wick_idx] -= spread[wick_idx] * rng.uniform(2, 5, len(wick_idx))
    volume[wick_idx] *= rng.integers(2, 6, len(wick_idx))

    return pd.DataFrame(
        {
            "time": times,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


# =========================================================
# FEATURES FOR SIMILAR DAY
# =========================================================
def add_features(df):
    work = normalize_ohlc(df)

    if work.empty:
        return work

    high = work["high"]
    low = work["low"]
    close = work["close"]
    prev_close = close.shift(1)

    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(14, min_periods=1).mean()

    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=work.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=work.index)

    atr_safe = atr.replace(0, np.nan)

    plus_di = 100 * plus_dm.rolling(14, min_periods=1).mean() / atr_safe
    minus_di = 100 * minus_dm.rolling(14, min_periods=1).mean() / atr_safe

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(14, min_periods=1).mean()

    work["atr"] = atr
    work["plus_di"] = plus_di
    work["minus_di"] = minus_di
    work["adx"] = adx
    work["pressure"] = plus_di - minus_di
    work["adx_slope"] = work["adx"].diff().fillna(0)
    work["atr_slope"] = work["atr"].diff().fillna(0)

    work["ret"] = work["close"].pct_change().fillna(0)
    work["log_ret"] = np.log(work["close"].replace(0, np.nan) / work["close"].shift(1).replace(0, np.nan))
    work["log_ret"] = work["log_ret"].replace([np.inf, -np.inf], 0).fillna(0)

    work["range"] = (work["high"] - work["low"]).replace(0, np.nan)
    work["body"] = (work["close"] - work["open"]).abs()
    work["wick_ratio"] = ((work["range"] - work["body"]) / work["range"]).replace([np.inf, -np.inf], 0).fillna(0)
    work["candle_efficiency"] = (work["body"] / work["range"]).replace([np.inf, -np.inf], 0).fillna(0)

    work["trend_power"] = work["adx"] * work["pressure"].abs()

    atr_mean = work["atr"].rolling(50, min_periods=1).mean().replace(0, np.nan)
    work["volatility_regime"] = (work["atr"] / atr_mean).replace([np.inf, -np.inf], 0).fillna(0)

    work["volatility_decay"] = (
        work["atr"].rolling(10, min_periods=1).mean()
        - work["atr"].rolling(50, min_periods=1).mean()
    ).replace([np.inf, -np.inf], 0).fillna(0)

    mean_120 = work["close"].rolling(120, min_periods=20).mean()
    std_120 = work["close"].rolling(120, min_periods=20).std().replace(0, np.nan)

    work["regression_to_mean_z"] = ((work["close"] - mean_120) / std_120).replace([np.inf, -np.inf], 0).fillna(0)

    ret_mean = work["log_ret"].rolling(120, min_periods=20).mean()
    ret_std = work["log_ret"].rolling(120, min_periods=20).std().replace(0, np.nan)

    work["ergodicity_proxy"] = (ret_mean / ret_std).replace([np.inf, -np.inf], 0).fillna(0)

    vol_mean = work["volume"].rolling(80, min_periods=10).mean().replace(0, np.nan)
    vol_std = work["volume"].rolling(80, min_periods=10).std().replace(0, np.nan)

    work["volume_z"] = ((work["volume"] - vol_mean) / vol_std).replace([np.inf, -np.inf], 0).fillna(0)

    work["spoofing_proxy"] = (
        work["wick_ratio"].clip(0, 1) * 45
        + (1 - work["candle_efficiency"].clip(0, 1)) * 35
        + work["volume_z"].abs().clip(0, 5) * 4
    ).replace([np.inf, -np.inf], 0).fillna(0)

    work["date"] = work["time"].dt.date
    work["date_ts"] = pd.to_datetime(work["date"])
    work["tod_minute"] = work["time"].dt.hour * 60 + work["time"].dt.minute

    return work.replace([np.inf, -np.inf], 0).fillna(0)


def window_vector(win, cols):
    arr = win[cols].astype(float).values
    arr = np.nan_to_num(arr, nan=0, posinf=0, neginf=0)

    mean = arr.mean(axis=0)
    std = arr.std(axis=0)
    change = arr[-1] - arr[0]
    last10 = arr[-10:].mean(axis=0) if len(arr) >= 10 else arr[-1]
    q10 = np.percentile(arr, 10, axis=0)
    q90 = np.percentile(arr, 90, axis=0)

    return np.concatenate([mean, std, change, last10, q10, q90])


def cosine_score(a, b):
    denom = np.linalg.norm(a) * np.linalg.norm(b) + 1e-12
    raw = float(np.dot(a, b) / denom)
    score = max(0, min(100, (raw + 1) * 50))
    return raw, score


def pca_score_numpy(all_vecs):
    if all_vecs.shape[0] < 3:
        return np.full(all_vecs.shape[0] - 1, 50.0)

    try:
        x = all_vecs - all_vecs.mean(axis=0)
        u, s, vt = np.linalg.svd(x, full_matrices=False)

        n_comp = min(6, vt.shape[0], all_vecs.shape[1], all_vecs.shape[0] - 1)

        coords = x @ vt[:n_comp].T
        current = coords[0]
        candidates = coords[1:]

        dist = np.linalg.norm(candidates - current, axis=1)
        med = max(float(np.median(dist)), 1e-9)

        return np.clip(100 * np.exp(-dist / med), 0, 100)

    except Exception:
        return np.full(all_vecs.shape[0] - 1, 50.0)


def kurtosis_value(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) < 8:
        return 3.0

    m = x.mean()
    s = x.std()

    if s == 0:
        return 3.0

    return float(np.mean(((x - m) / s) ** 4))


def max_drawdown_pct(log_rets):
    x = np.asarray(log_rets, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) == 0:
        return 0.0

    equity = np.exp(np.cumsum(x))
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / np.maximum(peak, 1e-12)

    return abs(float(dd.min()) * 100)


def monte_carlo_score(log_rets, horizon=120, paths=300, seed=1):
    x = np.asarray(log_rets, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) < 10:
        return 50.0, "UNKNOWN", 0.0, 0.0

    rng = np.random.default_rng(seed)

    horizon = int(max(5, min(horizon, 1000)))
    paths = int(max(50, min(paths, 2000)))

    sims = rng.choice(x, size=(paths, horizon), replace=True).sum(axis=1)
    moves = (np.exp(sims) - 1) * 100

    prob_up = float(np.mean(moves > 0))
    prob_down = 1 - prob_up

    bias = "BULLISH" if prob_up >= prob_down else "BEARISH"

    confidence = max(prob_up, prob_down)
    dispersion = float(np.std(moves))
    expected = float(np.mean(moves))
    stability = 1 / (1 + dispersion / 5)

    score = confidence * 75 + stability * 25

    return round(score, 2), bias, round(expected, 4), round(dispersion, 4)


# =========================================================
# SIMPLE SIMILAR DAY ENGINE
# =========================================================
def find_similar_days(df, lookback_days=100, window=120, horizon=120, top_n=10, mc_paths=300):
    work = add_features(df)

    if work.empty:
        return pd.DataFrame(), {"Status": "No usable data."}

    need = int(window + horizon + 50)

    if len(work) < need:
        return pd.DataFrame(), {
            "Status": f"Need more candles. Have {len(work)}, need at least {need}."
        }

    cols = [
        "ret",
        "log_ret",
        "adx",
        "plus_di",
        "minus_di",
        "atr",
        "pressure",
        "adx_slope",
        "atr_slope",
        "wick_ratio",
        "candle_efficiency",
        "trend_power",
        "volatility_regime",
        "volatility_decay",
        "regression_to_mean_z",
        "ergodicity_proxy",
        "spoofing_proxy",
    ]

    today_date = work["date_ts"].iloc[-1]
    yesterday = today_date - pd.Timedelta(days=1)
    start_date = today_date - pd.Timedelta(days=int(lookback_days))

    today_rows = work[work["date_ts"] == today_date]

    if len(today_rows) >= window:
        current_win = today_rows.tail(int(window)).copy()
    else:
        current_win = work.tail(int(window)).copy()

    current_end = current_win["time"].iloc[-1]
    current_tod = int(current_win["tod_minute"].iloc[-1])
    current_vec_raw = window_vector(current_win, cols)
    current_pressure = float(current_win["pressure"].mean())
    current_bias = 1 if current_pressure >= 0 else -1

    search = work[
        (work["date_ts"] >= start_date)
        & (work["date_ts"] < yesterday)
    ].copy()

    if len(search) < window:
        return pd.DataFrame(), {
            "Status": "Not enough older data after excluding today and yesterday. Load more candles."
        }

    candidates = []

    for day, day_df in search.groupby("date"):
        day_df = day_df.sort_values("time")

        if len(day_df) < window:
            continue

        best_for_day = None

        # Scan windows inside each day, then keep only best one per day.
        positions = list(range(window - 1, len(day_df), 20))

        same_time_pos = int((day_df["tod_minute"] - current_tod).abs().idxmin())
        positions.extend([same_time_pos, len(day_df) - 1])

        positions = sorted(set([p for p in positions if window - 1 <= p < len(day_df)]))

        for pos in positions:
            win = day_df.iloc[pos - window + 1 : pos + 1].copy()

            if len(win) < window:
                continue

            end_idx = int(win.index[-1])
            future_idx = end_idx + int(horizon)

            if future_idx >= len(work):
                continue

            vec = window_vector(win, cols)

            end_price = float(work.iloc[end_idx]["close"])
            future_price = float(work.iloc[future_idx]["close"])

            future_move = (future_price - end_price) / max(abs(end_price), 1e-12) * 100
            outcome = "BULLISH" if future_move > 0 else "BEARISH"

            cand_tod = int(work.iloc[end_idx]["tod_minute"])
            minutes = abs(cand_tod - current_tod)
            minutes = min(minutes, 1440 - minutes)

            fat_k = kurtosis_value(win["log_ret"].values)
            dd = max_drawdown_pct(win["log_ret"].values)

            fat_tail_score = max(0, min(100, 100 - max(0, fat_k - 3) * 8 - dd * 0.8))

            cur_vd = float(current_win["volatility_decay"].mean())
            cand_vd = float(win["volatility_decay"].mean())
            volatility_decay_score = max(0, min(100, 100 * math.exp(-abs(cur_vd - cand_vd) * 4)))

            cur_z = float(current_win["regression_to_mean_z"].iloc[-1])
            cand_z = float(win["regression_to_mean_z"].iloc[-1])
            regression_score = max(0, min(100, 100 * math.exp(-abs(cur_z - cand_z) / 2)))

            cur_ergo = float(current_win["ergodicity_proxy"].mean())
            cand_ergo = float(win["ergodicity_proxy"].mean())
            ergodicity_score = max(0, min(100, 100 * math.exp(-abs(cur_ergo - cand_ergo) * 4) - dd * 0.3))

            spoofing_risk = float(win["spoofing_proxy"].mean())
            spoofing_safety_score = max(0, min(100, 100 - spoofing_risk))

            mc_score, mc_bias, mc_expected, mc_dispersion = monte_carlo_score(
                win["log_ret"].values,
                horizon=horizon,
                paths=mc_paths,
                seed=int(end_idx * 17 + len(win) * 11) % 999983,
            )

            candidate = {
                "day": str(day),
                "end_time": work.iloc[end_idx]["time"],
                "minutes": int(minutes),
                "vec": vec,
                "future_move": float(future_move),
                "outcome": outcome,
                "fat_tail_score": float(fat_tail_score),
                "fat_kurtosis": float(fat_k),
                "max_drawdown_pct": float(dd),
                "volatility_decay_score": float(volatility_decay_score),
                "regression_score": float(regression_score),
                "ergodicity_score": float(ergodicity_score),
                "spoofing_safety_score": float(spoofing_safety_score),
                "spoofing_risk": float(spoofing_risk),
                "mc_score": float(mc_score),
                "mc_bias": mc_bias,
                "mc_expected": float(mc_expected),
                "mc_dispersion": float(mc_dispersion),
                "adx": float(win["adx"].mean()),
                "atr": float(win["atr"].mean()),
                "pressure": float(win["pressure"].mean()),
            }

            if best_for_day is None:
                best_for_day = candidate
            else:
                # temporary rough score by same time + low spoof/fat risk before final full ranking
                rough_current = abs(candidate["minutes"]) + candidate["spoofing_risk"] - candidate["fat_tail_score"]
                rough_best = abs(best_for_day["minutes"]) + best_for_day["spoofing_risk"] - best_for_day["fat_tail_score"]

                if rough_current < rough_best:
                    best_for_day = candidate

        if best_for_day is not None:
            candidates.append(best_for_day)

    if not candidates:
        return pd.DataFrame(), {
            "Status": "No valid similar days found. Load more candles or reduce pattern window."
        }

    matrix = np.vstack([current_vec_raw] + [c["vec"] for c in candidates])

    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0

    scaled = (matrix - mean) / std
    current_vec = scaled[0]
    cand_vecs = scaled[1:]

    pca_scores = pca_score_numpy(scaled)

    rows = []

    for i, c in enumerate(candidates):
        _, knn_score = cosine_score(current_vec, cand_vecs[i])
        pca_score = float(pca_scores[i])

        hist_bias = 1 if c["future_move"] >= 0 else -1

        feature_like = max(0.01, min(0.99, (knn_score * 0.65 + pca_score * 0.35) / 100))
        outcome_strength = 1 / (1 + math.exp(-abs(c["future_move"]) / 0.30))

        if hist_bias == current_bias:
            outcome_like = outcome_strength
        else:
            outcome_like = 1 - outcome_strength

        numerator = feature_like * outcome_like
        denominator = numerator + (1 - feature_like) * (1 - outcome_like) + 1e-12
        bayes_score = max(0, min(100, numerator / denominator * 100))

        time_score = max(0, 100 - (c["minutes"] / 360) * 100)

        final_score = (
            knn_score * 0.24
            + bayes_score * 0.14
            + pca_score * 0.13
            + c["fat_tail_score"] * 0.10
            + c["volatility_decay_score"] * 0.10
            + c["regression_score"] * 0.09
            + c["ergodicity_score"] * 0.08
            + c["spoofing_safety_score"] * 0.07
            + c["mc_score"] * 0.04
            + time_score * 0.01
        )

        rows.append(
            {
                "Most Similar Day": c["day"],
                "Most Similar Time": c["end_time"],
                "Minutes From Current Time": c["minutes"],
                "Final Rank Score": round(final_score, 2),
                "KNN Score": round(knn_score, 2),
                "Bayes Score": round(bayes_score, 2),
                "PCA Score": round(pca_score, 2),
                "Fat Tail Score": round(c["fat_tail_score"], 2),
                "Volatility Decay Score": round(c["volatility_decay_score"], 2),
                "Regression Mean Score": round(c["regression_score"], 2),
                "Ergodicity Score": round(c["ergodicity_score"], 2),
                "Spoofing Safety Score": round(c["spoofing_safety_score"], 2),
                "Monte Carlo Score": round(c["mc_score"], 2),
                "Monte Carlo Bias": c["mc_bias"],
                "MC Expected Move %": round(c["mc_expected"], 4),
                "Historical Future Move %": round(c["future_move"], 4),
                "Outcome": c["outcome"],
                "ADX": round(c["adx"], 2),
                "ATR": round(c["atr"], 5),
                "Pressure": round(c["pressure"], 2),
                "Fat Kurtosis": round(c["fat_kurtosis"], 2),
                "Max Drawdown %": round(c["max_drawdown_pct"], 3),
                "Spoofing Risk Proxy": round(c["spoofing_risk"], 2),
            }
        )

    result = pd.DataFrame(rows)

    # Absolute rule: no duplicate day.
    result = result.sort_values("Final Rank Score", ascending=False)
    result = result.drop_duplicates("Most Similar Day", keep="first")
    result = result.head(int(top_n)).reset_index(drop=True)
    result.insert(0, "Rank", range(1, len(result) + 1))

    bullish = float((result["Outcome"] == "BULLISH").mean() * 100) if len(result) else 50
    bearish = 100 - bullish

    summary = {
        "Status": "OK",
        "Current Window End": str(current_end),
        "Search": f"Last {lookback_days} days, excluding today and yesterday",
        "Returned Days": int(len(result)),
        "Dominant Bias": "BUY / BULLISH" if bullish > bearish else "SELL / BEARISH",
        "Bullish %": round(bullish, 1),
        "Bearish %": round(bearish, 1),
        "Top Score": float(result["Final Rank Score"].iloc[0]) if len(result) else 0,
    }

    return result, summary


# =========================================================
# ADVANCED HISTORY MATCH TAB
# =========================================================
def advanced_history_tab():
    st.markdown("# 🧠 Advanced History Matching")
    st.caption("Simple version: choose symbol, timeframe, and days. It finds similar historical days. This is not strategy backtesting.")

    st.markdown("## 🔌 Load Data")

    source = st.radio(
        "Data Source",
        ["Twelve Data", "MT5", "CSV Upload", "Session last_df", "Demo Data"],
        horizontal=True,
        key="pre_src",
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        default_symbol = "XAU/USD" if source == "Twelve Data" else "XAUUSD"
        symbol = st.text_input("Symbol", value=default_symbol, key="pre_symbol")

    with c2:
        tf = st.selectbox(
            "Timeframe",
            ["M1", "M2", "M3", "M5", "M15", "M30", "H1", "H4", "D1"],
            index=1,
            key="pre_tf",
        )

    with c3:
        lookback_days = st.number_input(
            "Lookback Days",
            min_value=10,
            max_value=250,
            value=100,
            step=5,
            key="pre_lookback_days",
        )

    with c4:
        top_n = st.number_input(
            "Top Result Days",
            min_value=5,
            max_value=50,
            value=10,
            step=1,
            key="pre_top_days",
        )

    c5, c6, c7 = st.columns(3)

    with c5:
        pattern_window = st.number_input(
            "Pattern Candles",
            min_value=60,
            max_value=300,
            value=120,
            step=10,
            key="pre_pattern_window",
        )

    with c6:
        future_horizon = st.number_input(
            "Future Move Candles",
            min_value=30,
            max_value=720,
            value=120,
            step=30,
            key="pre_future_horizon",
            help="Only shows what happened after similar days. It is not your strategy backtest.",
        )

    with c7:
        scan_bars = st.number_input(
            "Candles To Load",
            min_value=500,
            max_value=150000,
            value=90000 if source in ["MT5", "Demo Data"] else 5000,
            step=500,
            key="pre_candles_to_load",
        )

    api_key = ""
    csv_file = None
    demo_days = int(max(lookback_days + 30, 130))

    if source == "Twelve Data":
        default_key = get_secret_or_env("TWELVE_API_KEY", "TWELVE_DATA_API_KEY", default="")
        api_key = st.text_input("Twelve Data API Key", value=default_key, type="password", key="pre_td_key")
        st.caption("Note: Twelve Data free/limited plans often return only 5000 candles. For 100 days of M2 you need MT5, CSV, or Demo Data.")

    if source == "CSV Upload":
        csv_file = st.file_uploader("Upload CSV with time/open/high/low/close", type=["csv"], key="pre_csv")

    if source == "Demo Data":
        demo_days = st.slider("Demo Days", 30, 250, demo_days, 5, key="pre_demo_days")

    col_load, col_clear = st.columns(2)

    with col_load:
        load_clicked = st.button("🚀 Load Data", type="primary", use_container_width=True, key="pre_load_data")

    with col_clear:
        if st.button("🧹 Clear Loaded Data", use_container_width=True, key="pre_clear_data"):
            for k in [DATA_KEY, SOURCE_KEY, SYMBOL_KEY, TF_KEY, RESULT_KEY, SUMMARY_KEY]:
                st.session_state.pop(k, None)
            safe_rerun()

    if load_clicked:
        with st.spinner("Loading history data..."):
            if source == "Twelve Data":
                df, err = load_twelve(symbol, tf, int(scan_bars), api_key)
                final_symbol = twelve_symbol(symbol)

            elif source == "MT5":
                df, err = load_mt5(symbol, tf, int(scan_bars))
                final_symbol = mt5_symbol(symbol)

            elif source == "CSV Upload":
                if csv_file is None:
                    df = pd.DataFrame()
                    err = "Please upload CSV first."
                    final_symbol = "CSV"
                else:
                    try:
                        df = normalize_ohlc(pd.read_csv(csv_file))
                        df = resample_m2_m3(df, tf)
                        err = ""
                        final_symbol = "CSV"
                    except Exception as exc:
                        df = pd.DataFrame()
                        err = f"CSV failed: {exc}"
                        final_symbol = "CSV"

            elif source == "Session last_df":
                session_df = st.session_state.get("last_df")
                final_symbol = "Session last_df"

                try:
                    df = normalize_ohlc(session_df)
                    df = resample_m2_m3(df, tf)
                    err = "" if not df.empty else "Session last_df is empty or missing."
                except Exception as exc:
                    df = pd.DataFrame()
                    err = f"Session last_df failed: {exc}"

            else:
                df = make_demo_data(symbol=symbol, tf=tf, days=int(demo_days), seed=12)
                err = ""
                final_symbol = f"Demo {symbol}"

        if err:
            if "MetaTrader5 is not installed" in err:
                st.warning(err)
                st.info("MT5 needs local Windows MT5 terminal and `pip install MetaTrader5`. Use Twelve Data / CSV / Demo if MT5 is not available.")
            else:
                st.error(err)
            return

        if df.empty:
            st.error("Loaded data is empty.")
            return

        st.session_state[DATA_KEY] = df
        st.session_state[SOURCE_KEY] = source
        st.session_state[SYMBOL_KEY] = final_symbol
        st.session_state[TF_KEY] = tf
        st.session_state.pop(RESULT_KEY, None)
        st.session_state.pop(SUMMARY_KEY, None)

        st.success(f"Loaded {len(df):,} candles from {source}")
        safe_rerun()

    df = st.session_state.get(DATA_KEY)

    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("Load data first. For quick test, choose **Demo Data** and click Load Data.")
        return

    try:
        clean = normalize_ohlc(df)
    except Exception as exc:
        st.error(f"Loaded data invalid: {exc}")
        return

    source_loaded = st.session_state.get(SOURCE_KEY, "Unknown")
    symbol_loaded = st.session_state.get(SYMBOL_KEY, "Unknown")
    tf_loaded = st.session_state.get(TF_KEY, "Unknown")

    st.success(f"Connected: {source_loaded} | {symbol_loaded} | {tf_loaded} | Candles: {len(clean):,}")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Candles", f"{len(clean):,}")
    m2.metric("From", str(clean["time"].iloc[0]))
    m3.metric("To", str(clean["time"].iloc[-1]))
    m4.metric("Last Close", f"{clean['close'].iloc[-1]:.5f}")

    run = st.button("🧠 Find Similar Days", type="primary", use_container_width=True, key="pre_run_similarity")

    if run:
        with st.spinner("Finding similar days and ranking them..."):
            result, summary = find_similar_days(
                clean,
                lookback_days=int(lookback_days),
                window=int(pattern_window),
                horizon=int(future_horizon),
                top_n=int(top_n),
                mc_paths=300,
            )

        if result.empty:
            st.warning(summary.get("Status", "No result."))
            return

        st.session_state[RESULT_KEY] = result
        st.session_state[SUMMARY_KEY] = summary

    result = st.session_state.get(RESULT_KEY)
    summary = st.session_state.get(SUMMARY_KEY)

    if isinstance(result, pd.DataFrame) and not result.empty and isinstance(summary, dict):
        st.markdown("## ✅ Similar Day Ranking")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Dominant Bias", summary.get("Dominant Bias", "N/A"))
        s2.metric("Bullish %", summary.get("Bullish %", 0))
        s3.metric("Bearish %", summary.get("Bearish %", 0))
        s4.metric("Top Score", round(summary.get("Top Score", 0), 2))

        st.info(
            f"Current window end: {summary.get('Current Window End')} | "
            f"Search: {summary.get('Search')} | "
            f"Returned non-duplicate days: {summary.get('Returned Days')}"
        )

        if len(result) < int(top_n):
            st.warning(
                f"Only {len(result)} non-duplicate days found. "
                f"To get {top_n}+ days, load more candles/history."
            )

        st.dataframe(result, use_container_width=True, height=520)

        st.markdown("## ⬇️ Lowest Ranked In Returned Result")
        st.dataframe(result.sort_values("Final Rank Score", ascending=True), use_container_width=True, height=260)


# =========================================================
# PRE-TRADE CHECK TAB
# =========================================================
def pretrade_check_tab():
    st.markdown("# 📋 Pre-Trade Check")
    st.caption("Restored. This section was not removed.")

    items = [
        "Account Balance & Margin Checked",
        "Risk % per Trade Calculated",
        "Lot Size Verified",
        "Stop Loss & Take Profit Set",
        "Spread Acceptable",
        "No Major News / Economic Events",
        "M1 Direction Confirmed",
        "M5 Trend Alignment",
        "H1 / H4 Higher Timeframe Bias",
        "ADX Strength Valid",
        "+DI / -DI Alignment Strong",
        "Entry Candle Pattern Valid",
        "Support / Resistance Respected",
        "Volume / Liquidity OK",
        "Emotion & Psychology Clear",
        "Trading Plan Followed",
        "Internet & Platform Stable",
        "No Overtrading Signs",
        "Journal Ready to Log",
        "Exit Strategy Prepared",
    ]

    if "pretrade_check_restore" not in st.session_state:
        st.session_state.pretrade_check_restore = {item: False for item in items}

    c1, c2 = st.columns([1, 4])

    with c1:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.pretrade_check_restore = {item: False for item in items}
            safe_rerun()

    completed = 0

    for i, item in enumerate(items):
        checked = st.session_state.pretrade_check_restore.get(item, False)

        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(f"**{'✅' if checked else '⬜'} {item}**")

        with col2:
            if st.button("Toggle", key=f"precheck_toggle_{i}", use_container_width=True):
                st.session_state.pretrade_check_restore[item] = not checked
                safe_rerun()

        if checked:
            completed += 1

    total = len(items)
    progress = completed / total

    st.progress(progress)
    st.metric("Progress", f"{completed}/{total} — {progress * 100:.1f}%")

    if completed == total:
        st.success("✅ ALL SYSTEMS GO — READY FOR HIGH-PROBABILITY ENTRY")
        st.balloons()
    else:
        st.warning(f"⚠️ {total - completed} checks still pending.")
import math
import time
import pandas as pd
import streamlit as st


def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _exit_s(x, default=0.0):
    try:
        if x is None:
            return float(default)
        if isinstance(x, str) and x.strip() == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _clamp(x, low=0.0, high=100.0):
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return max(float(low), min(float(high), x))


def _softmax3(a, b, c):
    m = max(float(a), float(b), float(c))
    ea = math.exp(max(-60, min(60, float(a) - m)))
    eb = math.exp(max(-60, min(60, float(b) - m)))
    ec = math.exp(max(-60, min(60, float(c) - m)))
    total = ea + eb + ec

    if total <= 0:
        return 1 / 3, 1 / 3, 1 / 3

    return ea / total, eb / total, ec / total


def exit_survivability_tab():
    """
    FULL Exit Survivability inner tab.
    Paste this whole function over your old exit_survivability_tab().
    """

    st.markdown("# 🔥 EXIT SURVIVABILITY ENGINE")
    st.caption(
        "Hold Decision • Momentum Decay • Exhaustion Detection • Liquidity Trap • "
        "Edge Quality • Adaptive Exit Probability"
    )

    # =====================================================
    # STYLE
    # =====================================================
    st.markdown(
        """
        <style>
        .exit-card {
            background: linear-gradient(135deg, rgba(239,246,255,.95), rgba(248,250,252,.98));
            border: 1px solid #DCE7F7;
            border-radius: 16px;
            padding: 14px;
            margin: 8px 0 12px 0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, .06);
        }
        .exit-title {
            font-size: 18px;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .exit-sub {
            font-size: 12px;
            color: #475569;
            line-height: 1.45;
        }
        .danger-box {
            background: linear-gradient(135deg,#FEE2E2,#FECACA);
            border: 1px solid #FCA5A5;
            border-radius: 14px;
            padding: 12px;
            color: #7F1D1D;
            font-weight: 800;
            text-align: center;
        }
        .good-box {
            background: linear-gradient(135deg,#DCFCE7,#BBF7D0);
            border: 1px solid #86EFAC;
            border-radius: 14px;
            padding: 12px;
            color: #14532D;
            font-weight: 800;
            text-align: center;
        }
        .warn-box {
            background: linear-gradient(135deg,#FEF3C7,#FDE68A);
            border: 1px solid #FBBF24;
            border-radius: 14px;
            padding: 12px;
            color: #78350F;
            font-weight: 800;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # CLEAR FUNCTION
    # =====================================================
    def clear_exit_inputs():
        keys = [
            "exit_y_madx", "exit_y_plus", "exit_y_minus", "exit_y_atr",
            "exit_today_madx", "exit_today_plus", "exit_today_minus", "exit_today_atr",
            "exit_h1_madx", "exit_h1_plus", "exit_h1_minus", "exit_h1_atr",
            "exit_h2_madx", "exit_h2_plus", "exit_h2_minus", "exit_h2_atr",
            "exit_prev2_madx", "exit_prev2_plus", "exit_prev2_minus", "exit_prev2_atr",
            "exit_now2_madx", "exit_now2_plus", "exit_now2_minus", "exit_now2_atr",
            "exit_trade_direction",
            "exit_position_age_bars",
            "exit_entry_quality",
            "exit_risk_mode",
        ]

        for k in keys:
            if k in st.session_state:
                del st.session_state[k]

        safe_rerun()

    top_clear, top_info = st.columns([1, 4])

    with top_clear:
        if st.button(
            "🗑️ CLEAR EXIT INPUTS",
            type="secondary",
            use_container_width=True,
            key="exit_clear_all_full",
        ):
            clear_exit_inputs()

    with top_info:
        st.markdown(
            """
            <div class="exit-card">
                <div class="exit-title">Position survival dashboard</div>
                <div class="exit-sub">
                    Fill Daily, H4, and 2H values. This engine estimates HOLD, TRAIL,
                    PARTIAL EXIT, FULL EXIT, or EMERGENCY EXIT.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # =====================================================
    # INPUTS
    # =====================================================
    st.markdown("## 📥 Market Structure Inputs")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Yesterday")

        y_madx = st.number_input(
            "Yesterday MADX",
            value=None,
            key="exit_y_madx",
            step=0.1,
            format="%.2f",
        )
        y_plus = st.number_input(
            "Yesterday +DI",
            value=None,
            key="exit_y_plus",
            step=0.1,
            format="%.2f",
        )
        y_minus = st.number_input(
            "Yesterday -DI",
            value=None,
            key="exit_y_minus",
            step=0.1,
            format="%.2f",
        )
        y_atr = st.number_input(
            "Yesterday ATR",
            value=None,
            key="exit_y_atr",
            step=0.1,
            format="%.2f",
        )

        st.markdown("### Today Daily")

        today_madx = st.number_input(
            "Today MADX",
            value=None,
            key="exit_today_madx",
            step=0.1,
            format="%.2f",
        )
        today_plus = st.number_input(
            "Today +DI",
            value=None,
            key="exit_today_plus",
            step=0.1,
            format="%.2f",
        )
        today_minus = st.number_input(
            "Today -DI",
            value=None,
            key="exit_today_minus",
            step=0.1,
            format="%.2f",
        )
        today_atr = st.number_input(
            "Today ATR",
            value=None,
            key="exit_today_atr",
            step=0.1,
            format="%.2f",
        )

    with col2:
        st.markdown("### Previous H4 Block")

        h1_madx = st.number_input(
            "Prev H4 MADX",
            value=None,
            key="exit_h1_madx",
            step=0.1,
            format="%.2f",
        )
        h1_plus = st.number_input(
            "Prev H4 +DI",
            value=None,
            key="exit_h1_plus",
            step=0.1,
            format="%.2f",
        )
        h1_minus = st.number_input(
            "Prev H4 -DI",
            value=None,
            key="exit_h1_minus",
            step=0.1,
            format="%.2f",
        )
        h1_atr = st.number_input(
            "Prev H4 ATR",
            value=None,
            key="exit_h1_atr",
            step=0.1,
            format="%.2f",
        )

        st.markdown("### Current H4 Block")

        h2_madx = st.number_input(
            "Current H4 MADX",
            value=None,
            key="exit_h2_madx",
            step=0.1,
            format="%.2f",
        )
        h2_plus = st.number_input(
            "Current H4 +DI",
            value=None,
            key="exit_h2_plus",
            step=0.1,
            format="%.2f",
        )
        h2_minus = st.number_input(
            "Current H4 -DI",
            value=None,
            key="exit_h2_minus",
            step=0.1,
            format="%.2f",
        )
        h2_atr = st.number_input(
            "Current H4 ATR",
            value=None,
            key="exit_h2_atr",
            step=0.1,
            format="%.2f",
        )

    st.markdown("### 2H Micro Structure")

    mcol1, mcol2 = st.columns(2)

    with mcol1:
        st.markdown("**Previous 2H**")

        prev2_madx = st.number_input(
            "Prev 2H MADX",
            value=None,
            key="exit_prev2_madx",
            step=0.1,
            format="%.2f",
        )
        prev2_plus = st.number_input(
            "Prev 2H +DI",
            value=None,
            key="exit_prev2_plus",
            step=0.1,
            format="%.2f",
        )
        prev2_minus = st.number_input(
            "Prev 2H -DI",
            value=None,
            key="exit_prev2_minus",
            step=0.1,
            format="%.2f",
        )
        prev2_atr = st.number_input(
            "Prev 2H ATR",
            value=None,
            key="exit_prev2_atr",
            step=0.1,
            format="%.2f",
        )

    with mcol2:
        st.markdown("**Current 2H**")

        now2_madx = st.number_input(
            "Now 2H MADX",
            value=None,
            key="exit_now2_madx",
            step=0.1,
            format="%.2f",
        )
        now2_plus = st.number_input(
            "Now 2H +DI",
            value=None,
            key="exit_now2_plus",
            step=0.1,
            format="%.2f",
        )
        now2_minus = st.number_input(
            "Now 2H -DI",
            value=None,
            key="exit_now2_minus",
            step=0.1,
            format="%.2f",
        )
        now2_atr = st.number_input(
            "Now 2H ATR",
            value=None,
            key="exit_now2_atr",
            step=0.1,
            format="%.2f",
        )

    st.markdown("### Trade Context")

    t1, t2, t3 = st.columns(3)

    with t1:
        trade_direction = st.selectbox(
            "Your Current Trade Direction",
            ["BUY", "SELL"],
            key="exit_trade_direction",
        )

    with t2:
        position_age_bars = st.number_input(
            "Position Age / Bars Held",
            min_value=0,
            max_value=200,
            value=0,
            step=1,
            key="exit_position_age_bars",
        )

    with t3:
        entry_quality = st.selectbox(
            "Entry Quality",
            ["A+ High Conviction", "Good", "Average", "Weak"],
            index=1,
            key="exit_entry_quality",
        )

    risk_mode = st.selectbox(
        "Risk Mode",
        ["Normal", "Protect Profit", "Aggressive Hold", "Very Conservative"],
        index=0,
        key="exit_risk_mode",
    )

    # =====================================================
    # SAFE VALUES
    # =====================================================
    y_madx = _exit_s(y_madx)
    y_plus = _exit_s(y_plus)
    y_minus = _exit_s(y_minus)
    y_atr = _exit_s(y_atr)

    today_madx = _exit_s(today_madx)
    today_plus = _exit_s(today_plus)
    today_minus = _exit_s(today_minus)
    today_atr = _exit_s(today_atr)

    h1_madx = _exit_s(h1_madx)
    h1_plus = _exit_s(h1_plus)
    h1_minus = _exit_s(h1_minus)
    h1_atr = _exit_s(h1_atr)

    h2_madx = _exit_s(h2_madx)
    h2_plus = _exit_s(h2_plus)
    h2_minus = _exit_s(h2_minus)
    h2_atr = _exit_s(h2_atr)

    prev2_madx = _exit_s(prev2_madx)
    prev2_plus = _exit_s(prev2_plus)
    prev2_minus = _exit_s(prev2_minus)
    prev2_atr = _exit_s(prev2_atr)

    now2_madx = _exit_s(now2_madx)
    now2_plus = _exit_s(now2_plus)
    now2_minus = _exit_s(now2_minus)
    now2_atr = _exit_s(now2_atr)

    # =====================================================
    # CORE DERIVED VARIABLES
    # =====================================================
    daily_pressure = today_plus - today_minus
    yesterday_pressure = y_plus - y_minus

    h4_pressure_prev = h1_plus - h1_minus
    h4_pressure = h2_plus - h2_minus

    prev_micro_pressure = prev2_plus - prev2_minus
    micro_pressure = now2_plus - now2_minus

    pressure1 = h4_pressure_prev
    pressure2 = h4_pressure

    pressure_accel = pressure2 - pressure1
    micro_accel = micro_pressure - prev_micro_pressure
    daily_pressure_accel = daily_pressure - yesterday_pressure

    madx_accel = h2_madx - h1_madx
    micro_madx_accel = now2_madx - prev2_madx
    daily_madx_accel = today_madx - y_madx

    atr_accel = h2_atr - h1_atr
    micro_atr_accel = now2_atr - prev2_atr
    daily_atr_change = today_atr - y_atr

    madx_decay = h1_madx - h2_madx
    pressure_decay = h4_pressure_prev - h4_pressure
    atr_decay = h1_atr - h2_atr

    decay_velocity = h1_madx - h2_madx
    decay_acceleration = (h1_madx - h2_madx) - (today_madx - h1_madx)

    dominance1 = h1_plus / max(abs(h1_minus), 1.0)
    dominance2 = h2_plus / max(abs(h2_minus), 1.0)

    dominance_growth = dominance2 - dominance1

    pressure_variance = abs(h4_pressure - micro_pressure)
    atr_stability = _clamp(100 - abs(h2_atr - h1_atr) * 10, 0, 100)

    di_persistence = 0

    if today_plus > today_minus:
        di_persistence += 1
    if h1_plus > h1_minus:
        di_persistence += 1
    if h2_plus > h2_minus:
        di_persistence += 1
    if now2_plus > now2_minus:
        di_persistence += 1

    di_overlap = abs(now2_plus - now2_minus)
    noise_ratio = pressure_variance * 2

    micro_reversal_frequency = 0

    if prev2_plus > prev2_minus and now2_plus < now2_minus:
        micro_reversal_frequency += 1

    if prev2_plus < prev2_minus and now2_plus > now2_minus:
        micro_reversal_frequency += 1

    micro_reversals = micro_reversal_frequency

    if abs(micro_pressure) < 3:
        micro_reversals += 1

    peak_momentum = max(
        y_madx,
        today_madx,
        h1_madx,
        h2_madx,
        prev2_madx,
        now2_madx,
    )

    momentum_decay = peak_momentum - now2_madx

    if any([y_atr, today_atr, h1_atr, h2_atr, prev2_atr, now2_atr]):
        historical_atr_avg = (
            y_atr
            + today_atr
            + h1_atr
            + h2_atr
            + prev2_atr
            + now2_atr
        ) / 6
    else:
        historical_atr_avg = 0

    # =====================================================
    # BASIC DIRECTION STATE
    # =====================================================
    m1_direction = "BUY" if daily_pressure > 0 else "SELL"
    h4_direction = "BUY" if h4_pressure > 0 else "SELL"
    micro_direction = "BUY" if micro_pressure > 0 else "SELL"

    direction_alignment_count = sum(
        [
            m1_direction == trade_direction,
            h4_direction == trade_direction,
            micro_direction == trade_direction,
        ]
    )

    alignment = h4_direction == m1_direction

    # =====================================================
    # ORIGINAL DECAY / REVERSAL / PQS / SURVIVABILITY
    # =====================================================
    decay_score = 0

    if madx_decay > 2:
        decay_score += 25
    if pressure_decay > 4:
        decay_score += 30
    if atr_decay > 0.8:
        decay_score += 20
    if madx_accel < -2.5:
        decay_score += 28
    if atr_accel < -0.8:
        decay_score += 22
    if micro_pressure < 3 and trade_direction == "BUY":
        decay_score += 25
    if micro_pressure > -3 and trade_direction == "SELL":
        decay_score += 25
    if momentum_decay > 12:
        decay_score += 12
    if position_age_bars > 20 and decay_velocity > 1:
        decay_score += 8

    decay_score = _clamp(decay_score, 0, 95)

    reversal_threat = 0

    if madx_accel < -2.5:
        reversal_threat += 25
    if atr_accel < -1.0:
        reversal_threat += 22
    if abs(h4_pressure) > 15 and madx_accel < 0:
        reversal_threat += 20
    if trade_direction == "BUY" and micro_pressure < -5:
        reversal_threat += 30
    if trade_direction == "SELL" and micro_pressure > 5:
        reversal_threat += 30
    if direction_alignment_count <= 1:
        reversal_threat += 15
    if daily_pressure_accel * h4_pressure < 0:
        reversal_threat += 10

    reversal_threat = _clamp(reversal_threat, 0, 95)

    pqs = 68

    if h4_pressure > 10 and trade_direction == "BUY":
        pqs += 18
    if h4_pressure < -10 and trade_direction == "SELL":
        pqs += 18
    if madx_accel > 1.5:
        pqs += 15
    if micro_atr_accel > 0.3:
        pqs += 12
    if decay_score < 30:
        pqs += 14
    if direction_alignment_count == 3:
        pqs += 10
    if entry_quality == "A+ High Conviction":
        pqs += 8
    elif entry_quality == "Weak":
        pqs -= 10

    if decay_score > 50:
        pqs -= 25
    if reversal_threat > 50:
        pqs -= 28
    if atr_accel < -1.2:
        pqs -= 20

    if risk_mode == "Very Conservative":
        pqs -= 5
    elif risk_mode == "Aggressive Hold":
        pqs += 5

    pqs = _clamp(pqs, 10, 95)

    survivability = pqs - (decay_score * 0.45) - (reversal_threat * 0.35)

    if risk_mode == "Protect Profit":
        survivability -= 8
    elif risk_mode == "Aggressive Hold":
        survivability += 5
    elif risk_mode == "Very Conservative":
        survivability -= 12

    survivability = _clamp(survivability, 5, 95)

    # =====================================================
    # ADVANCED STRUCTURE VARIABLES
    # =====================================================
    stability = abs(pressure2) / (abs(pressure_accel) + 1)

    pressure_velocity = abs(pressure2) / (abs(pressure1) + 1)

    trend_efficiency = abs(pressure2) * h2_madx / (abs(pressure_accel) + 1)

    expansion_decay = abs(pressure_accel) / (abs(pressure2) + 1)

    expansion_quality = (
        trend_efficiency * 0.4
        + pressure_velocity * 0.3
        - expansion_decay * 0.3
    )

    exhaustion = abs(pressure2) > 20 and madx_accel < 0

    regime_score = 0

    if alignment:
        regime_score += 2
    if madx_accel > 0:
        regime_score += 1
    if pressure_accel > 0:
        regime_score += 1
    if dominance_growth > 0:
        regime_score += 1
    if stability > 3:
        regime_score += 1
    if abs(h4_pressure) > 10:
        regime_score += 1
    if abs(micro_pressure) > 5:
        regime_score += 1
    if exhaustion:
        regime_score -= 3
    if direction_alignment_count == 3:
        regime_score += 2
    if direction_alignment_count <= 1:
        regime_score -= 2

    environment_trust = (
        regime_score * 0.25
        + expansion_quality * 0.30
        + abs(h4_pressure) * 0.15
        + abs(micro_accel) * 0.10
        + stability * 0.15
        + di_persistence * 2.0
    )

    environment_trust = max(0, environment_trust)

    if environment_trust > 35:
        trust_level = "🔥 VERY HIGH"
    elif environment_trust > 24:
        trust_level = "🟢 HIGH"
    elif environment_trust > 14:
        trust_level = "🟡 MODERATE"
    else:
        trust_level = "🔴 LOW"

    reversal_risk = (
        expansion_decay * 0.35
        + (8 if abs(pressure2) > 20 else 0)
        + (6 if madx_accel < 0 else 0)
        + (5 if dominance_growth < 0 else 0)
        + (4 if stability < 2 else 0)
        + (10 if direction_alignment_count <= 1 else 0)
    )

    if reversal_risk > 24:
        reversal_state = "🚨 EXTREME REVERSAL RISK"
    elif reversal_risk > 13:
        reversal_state = "⚠️ REVERSAL POSSIBLE"
    else:
        reversal_state = "✅ STABLE CONTINUATION"

    continuation_probability = (environment_trust - reversal_risk) * 5
    continuation_probability = _clamp(continuation_probability, 0, 100)

    # =====================================================
    # LIQUIDITY / FALSE SIGNAL / EXECUTION ENGINE
    # =====================================================
    trap_score = (
        pressure_variance * 0.4
        + micro_reversal_frequency * 15
        + max(0, -madx_accel) * 2
    )

    trap_score = _clamp(trap_score, 0, 100)

    exec_stress = abs(atr_accel) * 10 + pressure_variance * 0.5
    exec_stress = _clamp(exec_stress, 0, 100)

    mqi = (
        atr_stability * 0.4
        + di_persistence * 15
        + abs(h4_pressure) * 1.5
    )

    mqi = _clamp(mqi, 0, 100)

    fsp = (
        pressure_variance * 0.35
        + max(0, -madx_accel) * 4
        + micro_reversal_frequency * 12
        + max(0, 5 - di_overlap) * 3
    )

    fsp = _clamp(fsp, 5, 95)

    ev = (continuation_probability / 100) * (abs(h4_pressure) / 10)
    ev = round(ev, 3)

    session_flow = (
        abs(h4_pressure) * 2
        + max(0, madx_accel) * 4
        + atr_stability * 0.4
    )

    session_flow = _clamp(session_flow, 0, 100)

    vqs = (
        atr_stability * 0.5
        + max(0, atr_accel) * 15
        + abs(h4_pressure) * 1.2
    )

    vqs = _clamp(vqs, 0, 100)

    regime_shift_prob = (
        max(0, -madx_accel) * 5
        + pressure_variance * 0.5
        + micro_reversal_frequency * 10
        + max(0, 8 - abs(h4_pressure)) * 3
    )

    regime_shift_prob = _clamp(regime_shift_prob, 0, 95)

    combined_trust = (
        environment_trust * 0.4
        + continuation_probability * 0.3
        + mqi * 0.3
    )

    combined_trust = _clamp(combined_trust, 0, 100)

    dist_to_liquidity = abs(h4_pressure) * 2
    wick_cluster = pressure_variance * 3

    liquidity_sweep_prob = (
        pressure_variance * 0.45
        + max(0, -madx_accel) * 6
        + micro_reversal_frequency * 18
        + max(0, 8 - abs(h4_pressure)) * 3
    )

    liquidity_sweep_prob = _clamp(liquidity_sweep_prob, 5, 95)

    liquidity_pressure = (
        abs(h4_pressure) * 2.2
        + abs(micro_pressure) * 1.5
        + max(0, madx_accel) * 5
        + atr_stability * 0.25
    )

    liquidity_pressure = _clamp(liquidity_pressure, 0, 100)

    if dist_to_liquidity < 25 and wick_cluster > 60:
        liq_zone = "Stop Cluster Zone (Dangerous)"
    elif dist_to_liquidity > 70:
        liq_zone = "Liquidity Void (Unstable)"
    elif 30 <= dist_to_liquidity <= 55:
        liq_zone = "Mid-Range Liquidity (Neutral)"
    else:
        liq_zone = "Liquidity Entry Zone (Safe Continuation)"

    breakout_failures = 0

    if pressure_accel > 0 and madx_accel < 0:
        breakout_failures += 1
    if abs(h4_pressure) > 12 and abs(micro_pressure) < 3:
        breakout_failures += 1
    if atr_accel < 0 and pressure_accel > 0:
        breakout_failures += 1
    if dominance_growth < 0:
        breakout_failures += 1

    hold_value = (
        environment_trust * 0.35
        + continuation_probability * 0.30
        + mqi * 0.20
        + atr_stability * 0.15
    )

    hold_value = _clamp(hold_value, 0, 100)

    candle_efficiency = (
        abs(h4_pressure) * 2
        + max(0, madx_accel) * 6
        + dominance_growth * 8
        - pressure_variance * 1.2
    )

    candle_efficiency = _clamp(candle_efficiency, 5, 100)

    # =====================================================
    # REGIME ADAPTIVE WEIGHTS
    # =====================================================
    adx_strength = h2_madx

    if adx_strength > 28 and noise_ratio < 40:
        regime = "🟢 TREND REGIME"
        regime_weight = 1.0
        decay_weight = 0.25
        liquidity_weight = 0.35
        reversal_weight = 0.20

    elif noise_ratio > 55 or di_overlap >= 4:
        regime = "🟡 TRANSITION / CHOPPY"
        regime_weight = 0.55
        decay_weight = 0.40
        liquidity_weight = 0.45
        reversal_weight = 0.35

    else:
        regime = "🔴 MANIPULATION / DISTRIBUTION"
        regime_weight = 0.35
        decay_weight = 0.30
        liquidity_weight = 0.60
        reversal_weight = 0.50

    momentum_conf = 0.85 if abs(h4_pressure) > 12 else 0.55

    contradiction_level = (
        "HIGH"
        if (decay_score > 60 and trap_score < 40)
        or (reversal_threat > 50 and hold_value > 70)
        else "MEDIUM"
        if abs(micro_pressure - h4_pressure) > 12
        else "LOW"
    )

    adjusted_survivability = survivability * regime_weight * momentum_conf
    adjusted_survivability = _clamp(adjusted_survivability, 0, 100)

    adaptive_exit_prob = (
        decay_score * decay_weight
        + trap_score * liquidity_weight
        + reversal_threat * reversal_weight
    )

    adaptive_exit_prob = _clamp(adaptive_exit_prob * max(0.35, regime_weight), 5, 98)

    final_prob = adaptive_exit_prob

    if risk_mode == "Protect Profit":
        final_prob += 8
    elif risk_mode == "Very Conservative":
        final_prob += 12
    elif risk_mode == "Aggressive Hold":
        final_prob -= 7

    final_prob = _clamp(final_prob, 5, 98)

    if final_prob >= 78 or ("Dangerous" in liq_zone and trap_score > 65):
        exit_type = "⚡ EMERGENCY EXIT (Liquidity Trap)"
    elif trap_score >= 65 or contradiction_level == "HIGH":
        exit_type = "🔴 FULL EXIT"
    elif decay_score > 45 or exec_stress > 60:
        exit_type = "🟠 PARTIAL EXIT"
    elif decay_velocity > 6:
        exit_type = "🟡 TRAIL STOP"
    else:
        exit_type = "🟢 HOLD"

    madx_z = (madx_accel / max(1, pressure_variance)) * 10
    decay_z = (decay_velocity - 5) / 8

    structural_conflict = abs(h4_pressure - micro_pressure) > 15
    tf_conflict = madx_accel > 0 and decay_velocity < -3

    if structural_conflict and tf_conflict:
        conflict_score = 85
    elif structural_conflict:
        conflict_score = 55
    else:
        conflict_score = 25

    half_life = 8 if momentum_decay <= 8 else 5 if momentum_decay <= 18 else 3

    p_continuation = 55 if regime == "🟢 TREND REGIME" else 35
    p_reversal = adaptive_exit_prob * 0.7
    p_manipulation = max(0, 100 - p_continuation - p_reversal)

    edge_score = 100 - (
        noise_ratio * 0.4
        + conflict_score * 0.4
        + (100 - regime_weight * 100) * 0.2
    )

    edge_score = _clamp(edge_score, 0, 100)

    if edge_score >= 70:
        edge_level = "HIGH EDGE"
    elif edge_score >= 45:
        edge_level = "WEAK EDGE"
    else:
        edge_level = "NO EDGE - UNRELIABLE"

    psi = (
        decay_score * 0.3
        + trap_score * 0.3
        + conflict_score * 0.2
        + exec_stress * 0.2
    )

    psi = _clamp(psi, 0, 98)

    base_threshold = (
        65
        if regime == "🟢 TREND REGIME"
        else 50
        if regime == "🟡 TRANSITION / CHOPPY"
        else 40
    )

    final_decision_threshold = base_threshold * (1 + conflict_score / 200)
    final_decision_threshold = _clamp(final_decision_threshold, 25, 95)

    mqs = (
        candle_efficiency * 0.4
        + atr_stability * 0.35
        + min(di_persistence * 8, 100) * 0.25
    )

    mqs = _clamp(mqs, 10, 100)

    tradeability = (
        mqs * 0.22
        + (100 - liquidity_pressure) * 0.18
        + mqi * 0.20
        + (100 - regime_shift_prob) * 0.15
        + session_flow * 0.15
        + combined_trust * 0.05
        + vqs * 0.05
    )

    tradeability = _clamp(tradeability, 10, 100)

    if tradeability >= 80:
        tradeability_level = "A+ Excellent"
    elif tradeability >= 60:
        tradeability_level = "Tradable"
    elif tradeability >= 40:
        tradeability_level = "Risky"
    else:
        tradeability_level = "Avoid"

    # =====================================================
    # ROLLING HISTORY / Z SCORE
    # =====================================================
    if "exit_history_full" not in st.session_state:
        st.session_state.exit_history_full = []

    st.session_state.exit_history_full.append(
        {
            "h4_pressure": h4_pressure,
            "mqs": mqs,
            "mqi": mqi,
            "liquidity_pressure": liquidity_pressure,
            "fsp": fsp,
        }
    )

    if len(st.session_state.exit_history_full) > 50:
        st.session_state.exit_history_full.pop(0)

    h4_z = 0.0

    if len(st.session_state.exit_history_full) > 5:
        pressures = [
            h.get("h4_pressure", 0)
            for h in st.session_state.exit_history_full
        ]

        mean_p = sum(pressures) / len(pressures)

        std_p = (
            sum((x - mean_p) ** 2 for x in pressures)
            / len(pressures)
        ) ** 0.5 + 1e-6

        h4_z = (h4_pressure - mean_p) / std_p

    trend_score = (h4_pressure * 0.4) + (mqs * 0.3) + (mqi * 0.3)

    chop_score = (
        liquidity_pressure * 0.4
        + fsp * 0.3
        + breakout_failures * 0.3
    )

    breakout_score = (abs(atr_accel) * 0.5) + (mqi * 0.5)

    p_trend, p_chop, p_breakout = _softmax3(
        trend_score / 50,
        chop_score / 50,
        breakout_score / 50,
    )

    prior_win = 0.50

    signal_strength = _clamp(
        (mqs + mqi + (100 - fsp)) / 300,
        0.01,
        0.99,
    )

    posterior_win = (
        prior_win * signal_strength
        / (
            prior_win * signal_strength
            + (1 - prior_win) * (1 - signal_strength)
            + 1e-12
        )
    )

    execution_cost = (
        (100 - atr_stability) * 0.10
        + breakout_failures * 5
        + micro_reversals * 3
    )

    execution_cost = _clamp(execution_cost, 0, 100)

    net_edge = ev * (1 - execution_cost / 100)

    # =====================================================
    # DISPLAY: FINAL DECISION
    # =====================================================
    st.markdown("---")
    st.markdown("## 🎯 Final Exit Recommendation")

    if "EMERGENCY" in exit_type or "FULL EXIT" in exit_type:
        st.markdown(
            f'<div class="danger-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )
    elif "PARTIAL" in exit_type or "TRAIL" in exit_type:
        st.markdown(
            f'<div class="warn-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="good-box">{exit_type}</div>',
            unsafe_allow_html=True,
        )

    d1, d2, d3, d4 = st.columns(4)

    d1.metric("Exit Probability", f"{final_prob:.1f}%")
    d2.metric("Survivability", f"{survivability:.1f}%")
    d3.metric("Adjusted Survival", f"{adjusted_survivability:.1f}%")
    d4.metric("Tradeability", f"{tradeability:.1f}/100", tradeability_level)

    st.progress(_clamp(survivability, 0, 100) / 100)

    # =====================================================
    # DISPLAY: CORE HOLD/EXIT
    # =====================================================
    st.markdown("## 🧱 Core Hold / Exit Metrics")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("H4 Pressure", f"{h4_pressure:.2f}", h4_direction)
    c2.metric("Micro Pressure", f"{micro_pressure:.2f}", micro_direction)
    c3.metric("Decay Score", f"{decay_score:.1f}%")
    c4.metric("Reversal Threat", f"{reversal_threat:.1f}%")

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Position Quality", f"{pqs:.1f}/100")
    c6.metric("Next 1-2H", "HOLD" if survivability > 50 else "MONITOR / EXIT")
    c7.metric("3-4H Risk", "HIGH" if reversal_threat > 50 else "LOW")
    c8.metric("Alignment", f"{direction_alignment_count}/3")

    if survivability >= 75 and reversal_threat < 35:
        st.success("🟢 STRONG HOLD — structure still supports the position.")
    elif survivability >= 55 and reversal_threat < 50:
        st.warning("🔵 HOLD CAUTIOUSLY — position can survive but monitor decay.")
    elif survivability >= 35:
        st.warning("🟠 PREPARE TO EXIT — survival is weakening.")
    else:
        st.error("🚨 EXIT / IMMEDIATE EXIT — position survivability is poor.")

    # =====================================================
    # DISPLAY: REGIME / EXPANSION
    # =====================================================
    st.markdown("## 🌐 Regime + Expansion Engine")

    r1, r2, r3, r4 = st.columns(4)

    r1.metric("Market Regime", regime)
    r2.metric("Regime Score", f"{regime_score}")
    r3.metric("Trust Level", trust_level)
    r4.metric("Continuation %", f"{continuation_probability:.1f}%")

    x1, x2, x3, x4 = st.columns(4)

    x1.metric("Pressure Accel", f"{pressure_accel:.2f}")
    x2.metric("MADX Accel", f"{madx_accel:.2f}")
    x3.metric("Dominance Growth", f"{dominance_growth:.2f}")
    x4.metric("Stability", f"{stability:.2f}")

    e1, e2, e3, e4 = st.columns(4)

    e1.metric("Pressure Velocity", f"{pressure_velocity:.2f}")
    e2.metric("Trend Efficiency", f"{trend_efficiency:.2f}")
    e3.metric("Expansion Decay", f"{expansion_decay:.2f}")
    e4.metric("Expansion Quality", f"{expansion_quality:.2f}")

    if expansion_quality > 25:
        st.success("🚀 HIGH QUALITY EXPANSION — strong sustainable directional pressure.")
    elif expansion_quality > 10:
        st.warning("⚠️ MODERATE EXPANSION — expansion exists but sustainability is uncertain.")
    else:
        st.error("❌ WEAK EXPANSION — fake breakout / reversal probability is higher.")

    rr1, rr2, rr3 = st.columns(3)

    rr1.metric("Reversal Risk", f"{reversal_risk:.2f}")
    rr2.metric("Reversal State", reversal_state)
    rr3.metric("Exhaustion", "YES" if exhaustion else "NO")

    if exhaustion:
        st.error("🚨 H4 EXHAUSTION DETECTED — trend may already be near completion.")

    # =====================================================
    # DISPLAY: LIQUIDITY / TRAP / CONFLICT
    # =====================================================
    st.markdown("## 🧲 Liquidity Trap + Conflict Engine")

    l1, l2, l3, l4 = st.columns(4)

    l1.metric("Liquidity Zone", liq_zone)
    l2.metric("Liquidity Sweep %", f"{liquidity_sweep_prob:.1f}%")
    l3.metric("Trap Score", f"{trap_score:.1f}/100")
    l4.metric("False Signal Prob", f"{fsp:.1f}%")

    l5, l6, l7, l8 = st.columns(4)

    l5.metric("Liquidity Pressure", f"{liquidity_pressure:.1f}")
    l6.metric("Signal Conflict", contradiction_level)
    l7.metric("Conflict Score", f"{conflict_score}/100")
    l8.metric("Breakout Failures", breakout_failures)

    if contradiction_level == "HIGH" or trap_score > 65:
        st.error("❌ High contradiction or trap pressure. Exit risk is elevated.")
    elif contradiction_level == "MEDIUM":
        st.warning("⚠️ Medium conflict. Trail stop or partial close may be better.")
    else:
        st.success("✅ Low conflict. Hold conditions are cleaner.")

    # =====================================================
    # DISPLAY: ADAPTIVE EXIT PROBABILITY
    # =====================================================
    st.markdown("## 🧠 Regime-Adaptive Exit Probability")

    a1, a2, a3, a4 = st.columns(4)

    a1.metric("Adaptive Exit %", f"{adaptive_exit_prob:.1f}%")
    a2.metric("Normalized MADX Z", f"{madx_z:.2f}")
    a3.metric("Decay Z", f"{decay_z:.2f}")
    a4.metric("Half-Life", f"{half_life} bars")

    p1, p2, p3 = st.columns(3)

    p1.metric("Continuation Scenario", f"{p_continuation:.1f}%")
    p2.metric("Sharp Reversal / Trap", f"{p_reversal:.1f}%")
    p3.metric("Sideways Manipulation", f"{p_manipulation:.1f}%")

    st.caption(
        "Regime-adaptive weights: trend/chop/manipulation modify how decay, "
        "liquidity, and reversal risk affect exit probability."
    )

    # =====================================================
    # DISPLAY: MARKET QUALITY
    # =====================================================
    st.markdown("## 📊 Market Quality + Tradeability")

    q1, q2, q3, q4 = st.columns(4)

    q1.metric("Market Quality Score", f"{mqs:.1f}/100")
    q2.metric("Market Quality Index", f"{mqi:.1f}/100")
    q3.metric("VQS", f"{vqs:.1f}/100")
    q4.metric("Session Flow", f"{session_flow:.1f}/100")

    q5, q6, q7, q8 = st.columns(4)

    q5.metric("ATR Stability", f"{atr_stability:.1f}%")
    q6.metric("Regime Shift Prob", f"{regime_shift_prob:.1f}%")
    q7.metric("Combined Trust", f"{combined_trust:.1f}%")
    q8.metric("Expected Value", f"{ev:.3f}R")

    st.metric("TRADEABILITY INDEX", f"{tradeability:.1f}/100 — {tradeability_level}")
    st.progress(tradeability / 100)

    # =====================================================
    # DISPLAY: STATISTICAL / BAYESIAN
    # =====================================================
    st.markdown("## 📈 Statistical + Bayesian Exit Layer")

    b1, b2, b3, b4 = st.columns(4)

    b1.metric("H4 Pressure Z-Score", f"{h4_z:.2f}")
    b2.metric("Trend Prob", f"{p_trend * 100:.1f}%")
    b3.metric("Chop Prob", f"{p_chop * 100:.1f}%")
    b4.metric("Breakout Prob", f"{p_breakout * 100:.1f}%")

    b5, b6, b7, b8 = st.columns(4)

    b5.metric("Bayesian Win Prob", f"{posterior_win * 100:.1f}%")
    b6.metric("Execution Cost", f"{execution_cost:.1f}%")
    b7.metric("Net Edge", f"{net_edge:.3f}R")
    b8.metric("Position Stress Index", f"{psi:.1f}/100")

    if edge_level == "NO EDGE - UNRELIABLE":
        st.error(edge_level)
    elif edge_level == "WEAK EDGE":
        st.warning(edge_level)
    else:
        st.success(edge_level)

    st.metric("Adaptive Exit Threshold", f"{final_decision_threshold:.1f}")

    # =====================================================
    # FULL DIAGNOSTIC TABLE
    # =====================================================
    st.markdown("## 🧾 Full Diagnostic Table")

    diag = pd.DataFrame(
        [
            ["Daily Pressure", daily_pressure],
            ["Yesterday Pressure", yesterday_pressure],
            ["Daily Pressure Accel", daily_pressure_accel],
            ["H4 Previous Pressure", h4_pressure_prev],
            ["H4 Current Pressure", h4_pressure],
            ["Micro Previous Pressure", prev_micro_pressure],
            ["Micro Current Pressure", micro_pressure],
            ["Micro Accel", micro_accel],
            ["MADX Accel", madx_accel],
            ["Micro MADX Accel", micro_madx_accel],
            ["Daily MADX Accel", daily_madx_accel],
            ["ATR Accel", atr_accel],
            ["Micro ATR Accel", micro_atr_accel],
            ["Daily ATR Change", daily_atr_change],
            ["MADX Decay", madx_decay],
            ["Pressure Decay", pressure_decay],
            ["ATR Decay", atr_decay],
            ["Decay Velocity", decay_velocity],
            ["Decay Acceleration", decay_acceleration],
            ["Momentum Decay", momentum_decay],
            ["Dominance Ratio Previous", dominance1],
            ["Dominance Ratio Current", dominance2],
            ["Dominance Growth", dominance_growth],
            ["Pressure Variance", pressure_variance],
            ["Noise Ratio", noise_ratio],
            ["DI Overlap", di_overlap],
            ["DI Persistence", di_persistence],
            ["Micro Reversal Frequency", micro_reversal_frequency],
            ["Micro Reversals", micro_reversals],
            ["Peak Momentum", peak_momentum],
            ["Historical ATR Avg", historical_atr_avg],
            ["Distance To Liquidity", dist_to_liquidity],
            ["Wick Cluster", wick_cluster],
            ["Candle Efficiency", candle_efficiency],
            ["Hold Value", hold_value],
            ["Environment Trust", environment_trust],
            ["Reversal Risk", reversal_risk],
            ["Continuation Probability", continuation_probability],
            ["Trap Score", trap_score],
            ["Exec Stress", exec_stress],
            ["FSP", fsp],
            ["EV", ev],
            ["Final Exit Probability", final_prob],
        ],
        columns=["Metric", "Value"],
    )

    diag["Value"] = diag["Value"].apply(
        lambda x: round(float(x), 4)
        if isinstance(x, (int, float))
        else x
    )

    st.dataframe(diag, use_container_width=True, hide_index=True)

    # =====================================================
    # MEMORY LOG
    # =====================================================
    st.markdown("## 📌 Setup Memory")

    if "exit_trade_memory_full" not in st.session_state:
        st.session_state.exit_trade_memory_full = []

    if st.button(
        "📌 Log Current Exit Snapshot",
        use_container_width=True,
        key="exit_log_snapshot",
    ):
        st.session_state.exit_trade_memory_full.append(
            {
                "time": pd.Timestamp.now(),
                "direction": trade_direction,
                "exit_type": exit_type,
                "survivability": survivability,
                "final_prob": final_prob,
                "pqs": pqs,
                "decay_score": decay_score,
                "reversal_threat": reversal_threat,
                "trap_score": trap_score,
                "tradeability": tradeability,
                "edge_level": edge_level,
            }
        )

        st.success("Exit snapshot logged.")

    if st.session_state.exit_trade_memory_full:
        st.dataframe(
            pd.DataFrame(st.session_state.exit_trade_memory_full).tail(20),
            use_container_width=True,
        )

    st.caption(
        "✅ Full Exit Survivability Engine active: decay, reversal, liquidity, "
        "conflict, Bayesian, execution stress, edge quality, adaptive threshold."
    )
def show():
    st.markdown("# 🧾 Original Pre Tab — Clean Restored")
    st.caption(
        "Advanced History Match + Pre-Trade Check + Exit Survivability. "
        "Combined 4H Bias and Main Decision are removed."
    )

    timer_panel()

    tabH, tabP, tabE = st.tabs(
        [
            "🧠 Advanced History Match",
            "📋 Pre-Trade Check",
            "🔥 Exit Survivability",
        ]
    )

    with tabH:
        advanced_history_tab()

    with tabP:
        pretrade_check_tab()

    with tabE:
        exit_survivability_tab()


if __name__ == "__main__":
    show()
