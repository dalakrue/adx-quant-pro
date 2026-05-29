import time
import streamlit as st
import streamlit.components.v1 as components

from .utils import safe_rerun


TIMER_END_KEY = "trade_end_time"
TIMER_RUNNING_KEY = "trade_timer_running"
TIMER_MINUTES_KEY = "trade_timer_minutes"


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
    try:
        minutes = int(minutes)
    except Exception:
        minutes = 240

    minutes = int(max(1, min(minutes, 1440)))

    st.session_state[TIMER_MINUTES_KEY] = minutes
    st.session_state[TIMER_END_KEY] = time.time() + minutes * 60
    st.session_state[TIMER_RUNNING_KEY] = True


def reset_trade_timer():
    st.session_state.pop(TIMER_END_KEY, None)
    st.session_state[TIMER_RUNNING_KEY] = False


def _sync_timer_finished():
    remaining = remaining_seconds()

    if remaining <= 0 and st.session_state.get(TIMER_RUNNING_KEY, False):
        st.session_state[TIMER_RUNNING_KEY] = False

    return remaining


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

    remaining = _sync_timer_finished()
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

            if (!value || !status) return;

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