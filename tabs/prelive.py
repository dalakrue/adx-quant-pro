import streamlit as st
import pandas as pd
import time

from core.data_connectors import manual_connect
from core.quant_models import add_indicators, quant_stack, pre_manual_decision
from core.common import safe_float, format_timer, remaining_time
from core.database import append_csv, read_csv


# ============================================================
# SAFE HELPERS — does not remove original system
# ============================================================

def _safe_append_csv(name, row):
    try:
        append_csv(name, row)
    except Exception as e:
        st.warning(f"History save skipped: {e}")


def _safe_read_csv(name):
    try:
        df = read_csv(name)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def _safe_remaining_time():
    """
    Uses your original remaining_time() first.
    If original common.py timer fails, this fallback keeps timer working.
    """
    try:
        rem = remaining_time()
        return int(max(0, rem))
    except Exception:
        end_time = st.session_state.get("timer_end_time")
        if not end_time:
            return 0
        try:
            return int(max(0, float(end_time) - time.time()))
        except Exception:
            return 0


def _safe_format_timer(seconds):
    try:
        return format_timer(seconds)
    except Exception:
        seconds = int(max(0, seconds))
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


def _sound_vibrate():
    st.markdown(
        """
        <audio autoplay>
            <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
        </audio>
        <script>
            if(navigator.vibrate){
                navigator.vibrate([500,200,500,200,800]);
            }
        </script>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# EMERGENCY PRE — API FREE
# ============================================================

def emergency_pre_inner():
    st.markdown("### 🚨 Original Emergency Pre — API Free")
    st.info("This inner tab intentionally does NOT connect to any API. Use it when MT5/Twelve is unavailable.")

    if "timer_minutes" not in st.session_state:
        st.session_state.timer_minutes = 120

    if "timer_end_time" not in st.session_state:
        st.session_state.timer_end_time = None

    c1, c2, c3 = st.columns(3)

    with c1:
        st.number_input(
            "Timer minutes / hours choice",
            min_value=1,
            max_value=1440,
            value=int(st.session_state.get("timer_minutes", 120)),
            key="timer_minutes"
        )

    with c2:
        if st.button("▶ Start 2H/Custom Timer", key="pre_timer_start", use_container_width=True):
            st.session_state.timer_end_time = time.time() + float(st.session_state.timer_minutes) * 60
            _safe_append_csv(
                "timer_history",
                {
                    "time": pd.Timestamp.now(),
                    "action": "start",
                    "minutes": st.session_state.timer_minutes
                }
            )
            st.rerun()

    with c3:
        if st.button("⏹ Stop Timer", key="pre_timer_stop", use_container_width=True):
            st.session_state.timer_end_time = None
            _safe_append_csv(
                "timer_history",
                {
                    "time": pd.Timestamp.now(),
                    "action": "stop",
                    "minutes": 0
                }
            )
            st.rerun()

    rem = _safe_remaining_time()

    c1, c2, c3 = st.columns(3)
    c1.metric("Remaining", _safe_format_timer(rem))
    c2.metric("Timer Minutes", st.session_state.get("timer_minutes", 120))
    c3.metric("Timer Status", "RUNNING" if st.session_state.get("timer_end_time") and rem > 0 else "STOPPED")

    if st.session_state.get("timer_end_time") and rem <= 0:
        st.error("🚨 TIMER FINISHED")
        _sound_vibrate()

    st.divider()

    st.markdown("#### 📍 Original DI Manual Inputs")

    c1, c2 = st.columns(2)

    with c1:
        plus_prev = st.text_input("+DI Prev", value=st.session_state.get("e_plus_prev", "22"), key="e_plus_prev")
        minus_prev = st.text_input("-DI Prev", value=st.session_state.get("e_minus_prev", "18"), key="e_minus_prev")

    with c2:
        plus_now = st.text_input("+DI Now", value=st.session_state.get("e_plus_now", "25"), key="e_plus_now")
        minus_now = st.text_input("-DI Now", value=st.session_state.get("e_minus_now", "20"), key="e_minus_now")

    selected = st.selectbox(
        "Trade decision you selected",
        ["WAIT", "BUY", "SELL", "EXIT", "HOLD"],
        key="pre_selected_decision"
    )

    if st.button("Run Original+ML Emergency Pre Model", use_container_width=True, key="pre_run_model"):
        try:
            res = pre_manual_decision(
                safe_float(plus_now),
                safe_float(minus_now),
                safe_float(plus_prev),
                safe_float(minus_prev),
                selected
            )

            if not isinstance(res, dict):
                res = {"manual_bias": "WAIT", "scale10": 0, "decision_quality_pct": 0, "pressure": 0, "comment": str(res)}

            _safe_append_csv(
                "pre_manual_runs",
                {
                    "time": pd.Timestamp.now(),
                    "selected": selected,
                    **res
                }
            )

            st.session_state.pre_result = res

        except Exception as e:
            st.session_state.pre_result = {
                "manual_bias": "ERROR",
                "scale10": 0,
                "decision_quality_pct": 0,
                "pressure": 0,
                "comment": f"Model error: {e}"
            }

    res = st.session_state.get("pre_result")

    if res:
        cols = st.columns(4)
        cols[0].metric("Manual Bias", res.get("manual_bias", "WAIT"))
        cols[1].metric("Quality /10", res.get("scale10", 0))
        cols[2].metric("Quality %", res.get("decision_quality_pct", 0))
        cols[3].metric("Pressure", res.get("pressure", 0))

        st.caption(res.get("comment", ""))

    with st.expander("Timer / Pre History"):
        st.markdown("##### Timer History")
        st.dataframe(_safe_read_csv("timer_history"), use_container_width=True)

        st.markdown("##### Pre Manual Runs")
        st.dataframe(_safe_read_csv("pre_manual_runs"), use_container_width=True)


# ============================================================
# MAIN PRELIVE TAB
# ============================================================

def show():
    st.markdown("# 📡 Prelive + Emergency Pre")

    if "symbol" not in st.session_state:
        st.session_state.symbol = "XAUUSD"

    if "twelve_api_key" not in st.session_state:
        st.session_state.twelve_api_key = ""

    tabs = st.tabs(["📡 Prelive API Data", "🚨 Emergency Pre API-Free"])

    with tabs[0]:
        prelive_symbol = st.text_input(
            "Symbol",
            value=st.session_state.get("symbol", "XAUUSD"),
            key="prelive_symbol"
        )

        st.session_state.symbol = prelive_symbol or "XAUUSD"

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Run MT5 1-Min View", use_container_width=True, key="prelive_run_mt5"):
                try:
                    manual_connect(
                        "mt5",
                        st.session_state.symbol,
                        st.session_state.get("twelve_api_key", ""),
                        bars=180
                    )
                    st.success("MT5 data loaded.")
                except Exception as e:
                    st.error(f"MT5 error: {e}")

        with c2:
            if st.button("Run Twelve 1-Min View", use_container_width=True, key="prelive_run_twelve"):
                try:
                    manual_connect(
                        "twelve",
                        st.session_state.symbol,
                        st.session_state.get("twelve_api_key", ""),
                        bars=180
                    )
                    st.success("Twelve data loaded.")
                except Exception as e:
                    st.error(f"Twelve API error: {e}")

        df = st.session_state.get("last_df")

        if df is None:
            st.warning("Click run button.")
            return

        if not isinstance(df, pd.DataFrame) or df.empty:
            st.error("No valid dataframe found from data connector.")
            return

        try:
            dfi = add_indicators(df).tail(120)
        except Exception as e:
            st.error(f"Indicator error: {e}")
            st.dataframe(df, use_container_width=True)
            return

        try:
            q = quant_stack(df, st.session_state.get("trade_history", []))
            if not isinstance(q, dict):
                q = {}
        except Exception as e:
            st.error(f"Quant model error: {e}")
            q = {}

        cols = st.columns(4)
        cols[0].metric("Prelive Bias", q.get("bias", "WAIT"))
        cols[1].metric("Quality /10", q.get("scale10", 0))
        cols[2].metric("Quality %", q.get("safe_pct", 0))
        cols[3].metric("ATR", q.get("atr", 0))

        chart_cols = [x for x in ["close", "adx", "pressure"] if x in dfi.columns]

        if "time" in dfi.columns and chart_cols:
            try:
                st.line_chart(dfi.set_index("time")[chart_cols])
            except Exception:
                st.line_chart(dfi[chart_cols])
        elif chart_cols:
            st.line_chart(dfi[chart_cols])
        else:
            st.warning("Chart skipped because close/adx/pressure columns are missing.")

        st.dataframe(dfi, use_container_width=True)

        try:
            _safe_append_csv(
                "prelive_snapshots",
                {
                    "time": pd.Timestamp.now(),
                    "symbol": st.session_state.symbol,
                    **q
                }
            )
        except Exception:
            pass

    with tabs[1]:
        emergency_pre_inner()