"""Version zero: the unmodified course policy, behind a legal-action guard."""
from hs_arena.agents.greedy_bot import GreedyBot
from actions import fallback, legal


def decide(state, config=None):
    action = GreedyBot("baseline", None).decide(state).action
    return action if legal(state, action) else fallback(state)
