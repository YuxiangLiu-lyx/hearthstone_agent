"""Versioned policy entry point; V0 is intentionally free of complex search."""
from baseline import decide as baseline_decide


def decide(state, config=None):
    return baseline_decide(state)
