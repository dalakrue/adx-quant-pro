import pandas as pd
import streamlit as st

from .connectors import safe_connect
from .shared_state import sync_backtest_keys_from_last_df, shared_data_status


def _safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass


def _top_shared_connector():
    st.markdown("# ⚡ Engine — Combined Control Center")
    st.caption("API connection is controlled once from the sidebar. This page only consumes shared st.session_state['last_df'].")

    df = st.session_state.get("last_df")
    rows = len(df) if isinstance(df, pd.DataFrame) else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Symbol", st.session_state.get("symbol", "XAUUSD"))
    c2.metric("Timeframe", st.session_state.get("timeframe", "M1"))
    c3.metric("Shared Rows", f"{rows:,}")
    c4.metric("Current Source", st.session_state.get("source", "DISCONNECTED"))

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Use sidebar connection in Backtest", use_container_width=True, key="engine_sync_sidebar_df"):
            sync_backtest_keys_from_last_df()
            st.success("Shared data synced into Engine / Prelive / Backtest.")
            _safe_rerun()
    with b2:
        if st.button("Clear Shared Data", use_container_width=True, key="combined_clear_shared"):
            for k in [
                "last_df", "connected", "source", "engine_shared_rows",
                "combined_original_backtest_raw_df",
                "combined_original_backtest_source",
                "combined_original_backtest_symbol",
                "combined_original_backtest_last_load",
            ]:
                st.session_state.pop(k, None)
            st.session_state.connected = False
            st.session_state.source = "DISCONNECTED"
            st.success("Shared data cleared.")
            _safe_rerun()

    ok, rows = shared_data_status()
    if ok:
        sync_backtest_keys_from_last_df()
        st.success(f"Shared data active: {rows:,} rows. Engine / Prelive / Backtest use the same loaded data.")
    else:
        st.info("No shared data yet. Use the global sidebar connector first.")

    st.divider()

def _call_original_show(module_name):
    try:
        if module_name == "engine":
            from . import original_engine_inner as mod
        elif module_name == "prelive":
            from . import original_prelive_inner as mod
        else:
            from . import original_backtest_inner as mod

        if hasattr(mod, "show"):
            mod.show()
        else:
            st.error(f"{module_name} module has no show() function.")

    except Exception as exc:
        st.error(f"{module_name} inner tab crashed safely: {exc}")
        with st.expander("Debug error"):
            st.exception(exc)


def show():
    _top_shared_connector()

    inner = st.tabs([
        "⚡ Engine Inner Tab",
        "📡 Prelive Inner Tab",
        "🧪 Backtest Original Inner Tab",
    ])

    with inner[0]:
        _call_original_show("engine")

    with inner[1]:
        _call_original_show("prelive")

    with inner[2]:
        sync_backtest_keys_from_last_df()
        _call_original_show("backtest")
