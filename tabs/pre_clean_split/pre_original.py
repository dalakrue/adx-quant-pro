import streamlit as st

from .timer import timer_panel
from .history_tab import advanced_history_tab
from .pretrade import pretrade_check_tab
from .exit_survivability import exit_survivability_tab


def _safe_run(title, func):
    """
    Runs each inner tab safely.
    If one tab has an error, the whole Pre tab will not crash.
    """
    try:
        func()
    except Exception as exc:
        st.error(f"{title} failed to load.")
        with st.expander("Show error detail"):
            st.exception(exc)


def show():
    st.markdown("# ✅ Clean Independent Pre Tab")
    st.caption(
        "Advanced History Match + Pre-Trade Check + Exit Survivability. "
        "Combined 4H Bias and Main Decision are removed."
    )

    st.divider()

    with st.container():
        _safe_run("Timer Panel", timer_panel)

    st.divider()

    tabH, tabP, tabE = st.tabs(
        [
            "🧠 Advanced History Match",
            "📋 Pre-Trade Check",
            "🔥 Exit Survivability",
        ]
    )

    with tabH:
        _safe_run("Advanced History Match", advanced_history_tab)

    with tabP:
        _safe_run("Pre-Trade Check", pretrade_check_tab)

    with tabE:
        _safe_run("Exit Survivability", exit_survivability_tab)


if __name__ == "__main__":
    show()