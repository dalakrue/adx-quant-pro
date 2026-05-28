import streamlit as st

from core.common import DEFAULT_TABS, log_event
from core.styles import request_close_sidebar


def _safe_log_event(message):
    try:
        log_event(message)
    except Exception:
        st.session_state.setdefault("activity_log", [])
        st.session_state.activity_log.insert(0, message)


def _init_sidebar_state():
    if "tab_choice" not in st.session_state:
        st.session_state.tab_choice = DEFAULT_TABS[0] if DEFAULT_TABS else "Home"

    if "symbol" not in st.session_state:
        st.session_state.symbol = "XAUUSD"

    if "phone_mode" not in st.session_state:
        st.session_state.phone_mode = False


def _set_mode(phone_mode: bool):
    st.session_state.phone_mode = phone_mode
    request_close_sidebar()
    st.rerun()


def _open_tab(tab):
    st.session_state.tab_choice = tab
    _safe_log_event(f"Open tab: {tab}")
    request_close_sidebar()
    st.rerun()


def sidebar_nav():
    _init_sidebar_state()

    with st.sidebar:
        st.markdown(
            """
            <div class="glass-card">
                <b>⚡ ADX Quant Pro</b><br>
                <small>Light ocean glass system</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_symbol = st.text_input(
            "Symbol",
            value=st.session_state.get("symbol", "XAUUSD"),
            key="sidebar_symbol",
            placeholder="XAUUSD / EURUSD / GBPUSD",
        )

        st.session_state.symbol = (nav_symbol or "XAUUSD").strip().upper()

        c1, c2 = st.columns(2)

        with c1:
            if st.button("📱 Tiny", use_container_width=True, key="nav_phone"):
                _set_mode(True)

        with c2:
            if st.button("🖥️ Wide", use_container_width=True, key="nav_wide"):
                _set_mode(False)

        current_mode = "📱 Tiny mobile" if st.session_state.phone_mode else "🖥️ Wide desktop"
        st.caption(f"Mode: {current_mode}")

        st.markdown("---")

        icons = {
            "Home": "🏠",
            "Engine": "⚡",
            "Backtest": "🧠",
            "Pre Original": "🧾",
            "Backtest Original": "📜",
            "Prelive": "📡",
            "Profile": "👤",
            "Risk": "🛡️",
            "Mix": "🧠",
            "Guide": "📘",
            "Settings": "⚙️",
        }

        for tab in DEFAULT_TABS:
            icon = icons.get(tab, "•")
            active = tab == st.session_state.get("tab_choice")

            label = f"✅ {icon} {tab}" if active else f"{icon} {tab}"

            if st.button(label, use_container_width=True, key=f"nav_{tab}"):
                _open_tab(tab)

        st.markdown("---")

        with st.expander("ℹ️ System Info", expanded=False):
            st.write("Symbol:", st.session_state.get("symbol", "XAUUSD"))
            st.write("Current Tab:", st.session_state.get("tab_choice", "Home"))
            st.write("Phone Mode:", st.session_state.get("phone_mode", False))

        st.caption(
            "Main Backtest = fast similar-day finder • Original Pre/Backtest are separate safe tabs • Risk/Doo Prime are inside Home"
        )

    return st.session_state.get("tab_choice", DEFAULT_TABS[0] if DEFAULT_TABS else "Home")