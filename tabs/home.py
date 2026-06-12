"""Compatibility loader for the refactored `tabs/home.py` module.

The original large file was split into `home_parts/part_*.py` chunks so no
active Python source file exceeds 500 lines. The chunks are executed in
this module namespace to preserve all existing imports and runtime behavior.
"""
from importlib import import_module as _import_module

_PARTS_PACKAGE = (__package__ + '.home_parts') if __package__ else 'home_parts'
_PART_COUNT = 6

_SOURCE = ""
for _idx in range(_PART_COUNT):
    _part = _import_module(f"{_PARTS_PACKAGE}.part_{_idx:03d}")
    _SOURCE += _part.SOURCE

exec(compile(_SOURCE, __file__, "exec"), globals(), globals())

del _idx, _part, _SOURCE, _import_module, _PARTS_PACKAGE, _PART_COUNT

# 2026-06-09 compact reliable Data Visualization / copy export patch
try:
    from .home_patch_20260609 import apply as _apply_home_patch_20260609
    _apply_home_patch_20260609(globals())
    del _apply_home_patch_20260609
except Exception as _home_patch_exc_20260609:
    try:
        import streamlit as st
        st.warning(f"Home reliability patch skipped: {_home_patch_exc_20260609}")
    except Exception:
        pass


# 2026-06-11 Finder Alignment Engine upgrade (non-destructive).
try:
    from .finder_alignment_upgrade_20260611 import install as _install_finder_alignment_upgrade_20260611
    _install_finder_alignment_upgrade_20260611(globals())
    del _install_finder_alignment_upgrade_20260611
except Exception as _finder_alignment_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"Finder alignment patch skipped: {_finder_alignment_exc_20260611}")
    except Exception:
        pass

# 2026-06-11 History Control Center + Power BI Visualization Control Center (additive only).
try:
    from .history_visual_controls_20260611 import install as _install_history_visual_controls_20260611
    _install_history_visual_controls_20260611(globals())
    del _install_history_visual_controls_20260611
except Exception as _history_visual_controls_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"History/Visualization control patch skipped: {_history_visual_controls_exc_20260611}")
    except Exception:
        pass
# 2026-06-11 KNN Priority Placement (display priority only; no ML prediction changes).
try:
    from .knn_priority_placement_20260611 import install as _install_knn_priority_placement_20260611
    _install_knn_priority_placement_20260611(globals())
    del _install_knn_priority_placement_20260611
except Exception as _knn_priority_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"KNN priority placement patch skipped: {_knn_priority_exc_20260611}")
    except Exception:
        pass


# 2026-06-11 Full advanced efficiency/reliability command upgrade (additive display layer only).
try:
    from .advanced_efficiency_control_20260611 import install as _install_advanced_efficiency_control_20260611
    _install_advanced_efficiency_control_20260611(globals())
    del _install_advanced_efficiency_control_20260611
except Exception as _advanced_efficiency_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"Advanced efficiency control patch skipped: {_advanced_efficiency_exc_20260611}")
    except Exception:
        pass

# 2026-06-11 Two-section clean Data Visualization final wrapper.
try:
    from .dv_two_section_clean_upgrade_20260611 import install as _install_dv_two_section_clean_upgrade_20260611
    _install_dv_two_section_clean_upgrade_20260611(globals())
    del _install_dv_two_section_clean_upgrade_20260611
except Exception as _dv_two_section_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"Data Visualization two-section clean patch skipped: {_dv_two_section_exc_20260611}")
    except Exception:
        pass
# 2026-06-11 Final priority/history/Data Visualization fix (display-only, non-destructive).
try:
    from .final_priority_history_dv_fix_20260611 import install as _install_final_priority_history_dv_fix_20260611
    _install_final_priority_history_dv_fix_20260611(globals())
    del _install_final_priority_history_dv_fix_20260611
except Exception as _final_priority_history_dv_exc_20260611:
    try:
        import streamlit as st
        st.warning(f"Final priority/history/Data Visualization patch skipped: {_final_priority_history_dv_exc_20260611}")
    except Exception:
        pass
# 2026-06-12 One merged run-gated Lunch section with Unified PowerBI regime sync.
try:
    from .lunch_unified_sync_run_gate_20260612 import install as _install_lunch_unified_sync_run_gate_20260612
    _install_lunch_unified_sync_run_gate_20260612(globals())
    del _install_lunch_unified_sync_run_gate_20260612
except Exception as _lunch_unified_sync_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Lunch unified sync patch skipped: {_lunch_unified_sync_exc_20260612}")
    except Exception:
        pass

# 2026-06-12 Data Visualization News/NLP + KNN/Greedy intelligence section.
try:
    from .dv_news_nlp_intelligence_20260612 import install as _install_dv_news_nlp_intelligence_20260612
    _install_dv_news_nlp_intelligence_20260612(globals())
    del _install_dv_news_nlp_intelligence_20260612
except Exception as _dv_news_nlp_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Data Visualization News/NLP patch skipped: {_dv_news_nlp_exc_20260612}")
    except Exception:
        pass

# 2026-06-12 Data Visualization Quant Structure Intelligence section.
try:
    from .dv_quant_structure_intelligence_20260612 import install as _install_dv_quant_structure_intelligence_20260612
    _install_dv_quant_structure_intelligence_20260612(globals())
    del _install_dv_quant_structure_intelligence_20260612
except Exception as _dv_quant_structure_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Data Visualization Quant Structure patch skipped: {_dv_quant_structure_exc_20260612}")
    except Exception:
        pass

# 2026-06-12 Final merged Data Visualization/Home intelligence + mobile app UI.
try:
    from .dv_home_unified_intelligence_20260612 import install as _install_dv_home_unified_intelligence_20260612
    _install_dv_home_unified_intelligence_20260612(globals())
    del _install_dv_home_unified_intelligence_20260612
except Exception as _dv_home_unified_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Final merged intelligence patch skipped: {_dv_home_unified_exc_20260612}")
    except Exception:
        pass

# 2026-06-12 Data Visualization research alignment: Random Forest + Regime/NLP history.
try:
    from .dv_research_alignment_20260612 import install as _install_dv_research_alignment_20260612
    _install_dv_research_alignment_20260612(globals())
    del _install_dv_research_alignment_20260612
except Exception as _dv_research_alignment_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Data Visualization research alignment patch skipped: {_dv_research_alignment_exc_20260612}")
    except Exception:
        pass


# 2026-06-12 final cleanup: synced PowerBI projection + Research moved into Home + auth copy sync.
try:
    from .final_research_projection_auth_sync_20260612 import install as _install_final_research_projection_auth_sync_20260612
    _install_final_research_projection_auth_sync_20260612(globals())
    del _install_final_research_projection_auth_sync_20260612
except Exception as _final_research_projection_auth_sync_exc_20260612:
    try:
        import streamlit as st
        st.warning(f"Final research/projection/auth sync patch skipped: {_final_research_projection_auth_sync_exc_20260612}")
    except Exception:
        pass
