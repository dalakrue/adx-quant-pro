import streamlit as st

try:
    from .helpers import init_profile_state
except Exception as e:
    init_profile_state = None
    INIT_ERROR = e
else:
    INIT_ERROR = None

try:
    from .styles import profile_css
except Exception as e:
    profile_css = None
    CSS_ERROR = e
else:
    CSS_ERROR = None

try:
    from .tabs import (
        render_overview_tab,
        render_market_core_logic_tab,
        render_guide_tab,
        render_saved_notes_tab,
        render_edit_profile_tab,
        render_trade_history_tab,
        render_settings_tab,
        render_activity_log_tab,
        render_train_data_tab,
        render_system_health_tab,
    )
except Exception as e:
    TAB_IMPORT_ERROR = e

    def _missing_tab(name):
        st.error(f"{name} tab could not load.")
        st.code(str(TAB_IMPORT_ERROR))

    def render_overview_tab():
        _missing_tab("Overview")

    def render_market_core_logic_tab():
        _missing_tab("Market Core Logic")

    def render_guide_tab():
        _missing_tab("Guide")

    def render_saved_notes_tab():
        _missing_tab("Saved Notes Viewer")

    def render_edit_profile_tab():
        _missing_tab("Edit Profile")

    def render_trade_history_tab():
        _missing_tab("Trade History")

    def render_settings_tab():
        _missing_tab("Settings")

    def render_activity_log_tab():
        _missing_tab("Activity Log")

    def render_train_data_tab():
        _missing_tab("Train Data")

    def render_system_health_tab():
        _missing_tab("System Health")


def _safe_render(tab_name, render_func):
    try:
        render_func()
    except Exception as e:
        st.error(f"{tab_name} crashed, but the full Profile Dashboard is still running.")
        st.code(str(e))


def _safe_init_profile_state():
    if init_profile_state is None:
        st.warning("Profile state helper could not load.")
        if INIT_ERROR:
            st.code(str(INIT_ERROR))
        return

    try:
        init_profile_state()
    except Exception as e:
        st.warning("Profile state initialization failed.")
        st.code(str(e))


def _safe_profile_css():
    if profile_css is None:
        if CSS_ERROR:
            st.warning("Profile CSS could not load. Dashboard will continue without custom CSS.")
            st.code(str(CSS_ERROR))
        return

    try:
        profile_css()
    except Exception as e:
        st.warning("Profile CSS failed. Dashboard will continue without custom CSS.")
        st.code(str(e))


def show():
    _safe_init_profile_state()
    _safe_profile_css()

    st.markdown("# 👤 Quant Profile Dashboard")

    tab_names = [
        "📄 Overview",
        "🧠 Market Core Logic",
        "📘 Guide",
        "📝 Saved Notes Viewer",
        "✏️ Edit Profile",
        "📊 Trade History",
        "⚙️ Settings",
        "📘 Activity Log",
        "🧪 Train Data",
        "🧰 System Health",
    ]

    renderers = [
        render_overview_tab,
        render_market_core_logic_tab,
        render_guide_tab,
        render_saved_notes_tab,
        render_edit_profile_tab,
        render_trade_history_tab,
        render_settings_tab,
        render_activity_log_tab,
        render_train_data_tab,
        render_system_health_tab,
    ]

    tabs = st.tabs(tab_names)

    for tab, tab_name, renderer in zip(tabs, tab_names, renderers):
        with tab:
            _safe_render(tab_name, renderer)