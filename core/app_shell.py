import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None

from core.common import init_state
from core.styles import apply_global_styles, auto_close_sidebar_script
from core.navigation import sidebar_nav
from core.data_connectors import maybe_refresh


def _safe_run_page(tab_name, show_func):
    try:
        show_func()
    except Exception as exc:
        st.error(f"{tab_name} page failed to load.")
        with st.expander("Show error detail"):
            st.exception(exc)


def _load_tab(tab):
    if tab == "Home":
        from tabs.home import show
        return show

    if tab == "Engine":
        from tabs.engine import show
        return show

    if tab == "Train Data":
        from tabs.train_data import show
        return show

    if tab == "Pre Original":
        from tabs.pre_original import show
        return show

    from tabs.profile import show
    return show


def run_app():
    st.set_page_config(
        page_title="M1 ADX Quant Pro",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    try:
        init_state()
    except Exception as exc:
        st.error("App state initialization failed.")
        st.exception(exc)
        return

    try:
        phone_mode = bool(st.session_state.get("phone_mode", False))
        apply_global_styles(phone_mode)
        auto_close_sidebar_script()
    except Exception as exc:
        st.warning("Styles failed to load, but the app will continue.")
        with st.expander("Show style error"):
            st.exception(exc)

    try:
        st_autorefresh(interval=600000, key="ten_min_refresh")
    except Exception:
        pass

    try:
        maybe_refresh(
            st.session_state.get("symbol", "XAUUSD"),
            st.session_state.get("twelve_api_key", ""),
            600,
            bridge_url=st.session_state.get("doo_bridge_url", ""),
            bridge_token=st.session_state.get("doo_bridge_token", ""),
        )
    except Exception as exc:
        st.warning("Auto data refresh failed. You can still use the app manually.")
        with st.expander("Show refresh error"):
            st.exception(exc)

    try:
        tab = sidebar_nav()
    except Exception as exc:
        st.error("Sidebar navigation failed.")
        st.exception(exc)
        return

    show = _load_tab(tab)
    _safe_run_page(tab, show)