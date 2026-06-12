import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None

from core.common import init_state
from core.styles import apply_global_styles
from core.navigation import sidebar_nav
from core.ui_relationship import init_ui_relationship_state, sync_shared_connection_signature
from core.system_contract import init_system_contract, maybe_persist_runtime_snapshot, update_data_quality_from_session
from core.app.lifecycle import _safe_run_page
from core.app.routes import load_tab
from core.app.refresh import run_deferred_refresh
from core.code_quality import run_light_maintenance
from core.pro_quality_upgrade import repair_session_contract
from core.global_upgrade import apply_extra_css, apply_dedup_metric_css
from core.pro_terminal_uiux import apply_pro_terminal_css, apply_pro_terminal_runtime_helpers, render_pro_command_center_bar, render_pro_popup_layer
from core.v6_final_ui_logic_patch import install_runtime as install_v6_runtime
from core.full_system_upgrade import apply_v21_uiux, render_popup
from core.streamlit_safe_dataframe import install_safe_dataframe_patch
from core.ui.app_polish import apply_next_level_uiux, render_real_app_header
from core.light_auth_20260612 import render_auth_gate


def run_app():
    try:
        install_safe_dataframe_patch()
    except Exception:
        pass

    try:
        st.set_page_config(page_title="M1 ADX Quant Pro", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")
    except Exception:
        pass

    try:
        init_state()
        init_system_contract()
        init_ui_relationship_state()
    except Exception as exc:
        st.error("App state initialization failed.")
        st.exception(exc)
        return

    try:
        phone_mode = bool(st.session_state.get("phone_mode", False))
        apply_global_styles(phone_mode)
        apply_extra_css()
        apply_dedup_metric_css()
        apply_pro_terminal_css()
        apply_pro_terminal_runtime_helpers()
        apply_v21_uiux()
        apply_next_level_uiux()
    except Exception as exc:
        st.warning("Styles failed to load, but the app will continue.")
        with st.expander("Show style error"):
            st.exception(exc)

    try:
        if not render_auth_gate():
            return
    except Exception as exc:
        st.error("Login gate failed. Guest mode can still be used after fixing the auth error.")
        st.exception(exc)
        return

    try:
        st_autorefresh(interval=600000, key="ten_min_refresh")
    except Exception:
        pass

    try:
        if st.session_state.get("ws_enabled", False):
            try:
                from core.websocket_feed import consume_websocket_into_session
                consume_websocket_into_session()
            except Exception:
                pass
        nav_age = __import__("time").time() - float(st.session_state.get("ui_navigation_click_ts", 0.0) or 0.0)
        fast_nav = bool(st.session_state.get("fast_tab_switch_active", False)) or nav_age < 2.5
        if not fast_nav:
            run_deferred_refresh()
            run_light_maintenance()
            repair_session_contract()
        else:
            st.session_state["deferred_auto_refresh_reason"] = "Skipped refresh/maintenance for fast tab switch."
    except Exception as exc:
        st.warning("Auto data refresh failed. You can still use the app manually.")
        with st.expander("Show refresh error"):
            st.exception(exc)

    try:
        update_data_quality_from_session(persist=False)
        sync_shared_connection_signature()
        maybe_persist_runtime_snapshot("app_cycle")
    except Exception:
        pass

    try:
        tab = sidebar_nav()
    except Exception as exc:
        st.error("Sidebar navigation failed.")
        st.exception(exc)
        return

    try:
        render_pro_popup_layer()
        render_popup()
        render_real_app_header(tab)
        render_pro_command_center_bar(tab)
        install_v6_runtime(tab)
    except Exception:
        pass

    show = load_tab(tab)
    _safe_run_page(tab, show)
    st.session_state["fast_tab_switch_active"] = False
