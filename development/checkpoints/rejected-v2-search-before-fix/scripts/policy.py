"""Official policy plus a conservative bounded tactical proof search."""
from hs_arena.agents.greedy_bot import GreedyBot
from actions import fallback, legal
from planner import lethal_plan

def decide(state, config=None):
 config=config or {}
 if state['phase']=='game_over':return None
 if state['phase']=='main' and config.get('search',True):
  plan=lethal_plan(state,budget_s=config.get('search_budget_s',.035),max_nodes=config.get('search_nodes',700))
  if plan:return plan[0]
 action=GreedyBot('baseline',None).decide(state).action
 return action if legal(state,action) else fallback(state)
