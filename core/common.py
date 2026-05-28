import streamlit as st
import pandas as pd
import numpy as np
import time


# Reduced sidebar choices: Mix is inside Engine, Risk + Doo Prime are inside Home, Pre is inside Prelive.
DEFAULT_TABS = [
    "Home",
    "Engine",
    "Backtest",
    "Pre Original",
    "Backtest Original",
    "Prelive",
    "Profile",
]


def safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        if str(v).strip() == "":
            return default
        return float(v)
    except Exception:
        return default


def safe_int(v, default=0):
    try:
        if v is None:
            return default
        if str(v).strip() == "":
            return default
        return int(float(v))
    except Exception:
        return default


def init_state():
    defaults = {
        "tab_choice": "Home",
        "symbol": "XAUUSD",
        "phone_mode": False,

        "connected": False,
        "source": "DISCONNECTED",
        "last_df": None,
        "last_fetch": 0,
        "timeframe": "M1",

        "timer_end_time": None,
        "trade_end_time": None,
        "timer_minutes": 120,

        "activity_log": [],
        "notes": [],
        "trade_history": [],
        "profile_name": "Quant Trader",

        "twelve_api_key": "",
        "account_snapshot": {},
        "doo_positions": [],

        "training_rows": [],
        "guide_restored": True,

        "risk_mode": "Balanced",
        "setting_auto_entry": True,
        "setting_exit_alerts": True,
        "setting_risk_active": True,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def log_event(msg):
    try:
        if "activity_log" not in st.session_state:
            st.session_state.activity_log = []

        st.session_state.activity_log.insert(
            0,
            {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "event": str(msg),
            },
        )

        st.session_state.activity_log = st.session_state.activity_log[:500]

    except Exception:
        pass


def format_timer(seconds):
    try:
        seconds = max(0, int(seconds))
    except Exception:
        seconds = 0

    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    return f"{h:02d}:{m:02d}:{s:02d}"


def remaining_time():
    end = st.session_state.get("timer_end_time")

    if not end:
        end = st.session_state.get("trade_end_time")

    if not end:
        return 0

    try:
        return max(0, int(float(end) - time.time()))
    except Exception:
        return 0


def remaining_seconds():
    return remaining_time()


def start_timer(minutes=None):
    if minutes is None:
        minutes = st.session_state.get("timer_minutes", 120)

    minutes = safe_float(minutes, 120)

    end_time = time.time() + minutes * 60

    st.session_state.timer_end_time = end_time
    st.session_state.trade_end_time = end_time

    log_event(f"Timer started: {minutes} minutes")

    return end_time


def stop_timer():
    st.session_state.timer_end_time = None
    st.session_state.trade_end_time = None
    log_event("Timer stopped")


def synthetic_ohlc(symbol="XAUUSD", bars=1500):
    bars = max(50, safe_int(bars, 1500))
    symbol = str(symbol or "XAUUSD").upper()

    rng = np.random.default_rng(abs(hash(symbol)) % (2**32))

    if "XAU" in symbol:
        base = 2350
        scale = 0.70
    elif "JPY" in symbol:
        base = 150
        scale = 0.025
    elif "EUR" in symbol:
        base = 1.08
        scale = 0.00025
    elif "GBP" in symbol:
        base = 1.27
        scale = 0.00035
    else:
        base = 100
        scale = 0.10

    steps = rng.normal(0, scale, bars).cumsum()
    close = base + steps
    open_ = np.r_[close[0], close[:-1]]

    high = np.maximum(open_, close) + np.abs(rng.normal(0, scale * 0.5, bars))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, scale * 0.5, bars))

    volume = rng.integers(100, 3000, size=bars)

    return pd.DataFrame(
        {
            "time": pd.date_range(
                end=pd.Timestamp.now(),
                periods=int(bars),
                freq="min",
            ),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def normalize_symbol(symbol="XAUUSD"):
    symbol = str(symbol or "XAUUSD").strip().upper()
    return symbol.replace(" ", "")


def is_phone_mode():
    return bool(st.session_state.get("phone_mode", False))