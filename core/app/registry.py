"""Central tab/module registry for flexible future upgrades.

To add a new tab later, only add one entry to TAB_REGISTRY and one name to
core.common.DEFAULT_TABS. The app shell will lazy-import the module, so one
broken tab will not crash the whole application.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TabSpec:
    name: str
    module: str
    function: str = "show"
    icon: str = "📌"
    layer: str = "tab"
    notes: str = ""


TAB_REGISTRY: Dict[str, TabSpec] = {
    "Lunch": TabSpec("Lunch", "tabs.home", icon="🍱", layer="tab", notes="Lunch command center. Metric and 010 reverse decision run only after Run Calculating."),
    "Research": TabSpec("Research", "tabs.research", icon="🎓", layer="tab", notes="Final-year CS research workspace: Data Analysis, Data Mining, and NLP; all run-gated."),
    "Other": TabSpec("Other", "tabs.other", icon="📂", layer="tab", notes="Lazy inner workspace for Engine, Train Data, Database, Pre Original, and Profile."),
    # Kept for backward compatibility only. It is no longer shown in the sidebar.
    "Metric": TabSpec("Metric", "tabs.eurusd_h1_matrix", icon="📊", layer="inner", notes="EURUSD H1 decision metric inner section."),
}


def get_tab_spec(tab_name: str) -> TabSpec:
    """Return a valid tab spec, falling back to Lunch for unknown names."""
    return TAB_REGISTRY.get(str(tab_name), TAB_REGISTRY["Lunch"])


def tab_icons() -> dict:
    """Small helper for navigation buttons without duplicating icon maps."""
    return {name: spec.icon for name, spec in TAB_REGISTRY.items()}
