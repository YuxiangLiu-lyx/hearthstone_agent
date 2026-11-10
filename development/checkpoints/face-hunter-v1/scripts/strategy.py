"""Versioned policy entry point; V0 is intentionally free of complex search."""
from baseline import decide as baseline_decide


def decide(state, config=None):
    config = config or {}
    if config.get("lethal") and state.get("phase") == "main":
        from lethal_planner import search
        plan = search(state, budget_s=config.get("search_budget_s", .06),
                      max_nodes=config.get("search_nodes", 1600))
        if plan["guaranteed"]:
            return plan["first_action"]
    return baseline_decide(state)
