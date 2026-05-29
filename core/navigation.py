import streamlit as st

from core.common import DEFAULT_TABS, log_event
from core.styles import request_close_sidebar


def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _safe_log_event(message):
    try:
        log_event(message)
    except Exception:
        try:
            st.session_state.setdefault("activity_log", [])
            st.session_state.activity_log.insert(0, str(message))
        except Exception:
            pass


def _init_sidebar_state():
    if "tab_choice" not in st.session_state:
        st.session_state.tab_choice = DEFAULT_TABS[0] if DEFAULT_TABS else "Home"

    if st.session_state.tab_choice not in DEFAULT_TABS:
        st.session_state.tab_choice = DEFAULT_TABS[0] if DEFAULT_TABS else "Home"

    if "symbol" not in st.session_state:
        st.session_state.symbol = "XAUUSD"

    if "phone_mode" not in st.session_state:
        st.session_state.phone_mode = False


def _normalize_symbol(symbol):
    symbol = str(symbol or "XAUUSD").strip().upper()
    return symbol.replace(" ", "").replace("/", "")


def _set_mode(phone_mode: bool):
    st.session_state.phone_mode = bool(phone_mode)
    request_close_sidebar()
    _safe_rerun()


def _open_tab(tab):
    st.session_state.tab_choice = tab
    _safe_log_event(f"Open tab: {tab}")
    request_close_sidebar()
    _safe_rerun()


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

        st.session_state.symbol = _normalize_symbol(nav_symbol)

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
        st.markdown("### 🔌 Global API Connector")
        st.caption("Choose once here. All tabs use this shared connection.")

        connector_mode = st.selectbox(
            "API source",
            ["fallback", "mt5", "twelve", "doo_bridge"],
            index=["fallback", "mt5", "twelve", "doo_bridge"].index(st.session_state.get("connector_mode", "fallback")) if st.session_state.get("connector_mode", "fallback") in ["fallback", "mt5", "twelve", "doo_bridge"] else 0,
            key="sidebar_connector_mode",
            help="MT5 works only where MetaTrader5 terminal/library is available. Streamlit Cloud usually needs Twelve Data or Doo Bridge.",
        )
        st.session_state.connector_mode = connector_mode

        timeframe = st.selectbox(
            "Timeframe",
            ["M1", "M2", "M3", "M5", "M10", "M15", "M30", "H1", "H4", "D1"],
            index=0 if st.session_state.get("timeframe", "M1") not in ["M1", "M2", "M3", "M5", "M10", "M15", "M30", "H1", "H4", "D1"] else ["M1", "M2", "M3", "M5", "M10", "M15", "M30", "H1", "H4", "D1"].index(st.session_state.get("timeframe", "M1")),
            key="sidebar_timeframe",
        )
        st.session_state.timeframe = timeframe

        bars = st.number_input(
            "Candles / bars",
            min_value=100,
            max_value=250000,
            value=int(st.session_state.get("connector_bars", 5000)),
            step=100,
            key="sidebar_connector_bars",
        )
        st.session_state.connector_bars = int(bars)

        if connector_mode == "twelve":
            st.session_state.twelve_api_key = st.text_input(
                "Twelve Data API key",
                value=st.session_state.get("twelve_api_key", ""),
                type="password",
                key="sidebar_twelve_api_key",
            )
        elif connector_mode == "doo_bridge":
            st.session_state.doo_bridge_url = st.text_input(
                "Doo Bridge URL",
                value=st.session_state.get("doo_bridge_url", ""),
                key="sidebar_doo_bridge_url",
                placeholder="http://127.0.0.1:8000/candles or your bridge endpoint",
            )
            st.session_state.doo_bridge_token = st.text_input(
                "Doo Bridge token optional",
                value=st.session_state.get("doo_bridge_token", ""),
                type="password",
                key="sidebar_doo_bridge_token",
            )
        elif connector_mode == "mt5":
            st.info("MT5 requires the local MT5 terminal open and logged in. It usually will not run directly on Streamlit Cloud.")

        conn_cols = st.columns(2)
        with conn_cols[0]:
            if st.button("Connect API", use_container_width=True, key="sidebar_connect_api"):
                try:
                    from core.data_connectors import manual_connect
                    df, ok, source, msg = manual_connect(
                        mode=st.session_state.connector_mode,
                        symbol=st.session_state.symbol,
                        api_key=st.session_state.get("twelve_api_key", ""),
                        bars=int(st.session_state.connector_bars),
                        timeframe=st.session_state.timeframe,
                        bridge_url=st.session_state.get("doo_bridge_url", ""),
                        bridge_token=st.session_state.get("doo_bridge_token", ""),
                    )
                    if ok:
                        st.success(f"Connected {source}: {len(df):,} rows")
                    else:
                        st.warning(str(msg))
                    _safe_rerun()
                except Exception as exc:
                    st.error(f"Connect failed: {exc}")
        with conn_cols[1]:
            if st.button("Disconnect", use_container_width=True, key="sidebar_disconnect_api"):
                for k in ["connected", "source", "last_df", "last_fetch"]:
                    st.session_state.pop(k, None)
                st.session_state.connected = False
                st.session_state.source = "DISCONNECTED"
                st.success("Disconnected.")
                _safe_rerun()

        rows = 0
        try:
            rows = len(st.session_state.get("last_df")) if st.session_state.get("last_df") is not None else 0
        except Exception:
            rows = 0
        st.caption(f"Shared source: {st.session_state.get('source', 'DISCONNECTED')} | Rows: {rows:,}")

        icons = {
            "Home": "🏠",
            "Engine": "⚡",
            "Train Data": "🧠",
            "Pre Original": "🧾",
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
            st.write("Connected:", st.session_state.get("connected", False))
            st.write("Source:", st.session_state.get("source", "DISCONNECTED"))
            st.write("Timeframe:", st.session_state.get("timeframe", "M1"))

        st.caption(
            "Main Backtest = fast similar-day finder • Original Pre/Backtest are separate safe tabs • Risk/Doo Prime are inside Home"
        )

    return st.session_state.get("tab_choice", DEFAULT_TABS[0] if DEFAULT_TABS else "Home")