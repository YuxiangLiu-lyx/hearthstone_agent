"""One publication-based budget, translated to monotonic time on every invocation."""
import time


class Budget:
    def __init__(self,state,config):
        self.cfg=config['budgets'];now=time.time();mono=time.monotonic()
        deadline=float(state.get('deadline_epoch_s',now+state.get('timeout_s',180)))
        published=deadline-float(state.get('timeout_s',180))
        self.official=mono+deadline-now
        self.target=mono+min(published+self.cfg['target_s'],deadline-self.cfg['reserve_s'])-now
        self.adopt=mono+min(published+self.cfg['adopt_s'],deadline-self.cfg['reserve_s'])-now
        self.published=published

    def remaining(self):return max(0.,self.official-time.monotonic())
    def accepts_model(self):return time.monotonic()<self.adopt
    def tool_limit(self,deep=False):
        cap=self.cfg['deep_s'] if deep else self.cfg['default_s']
        return max(0.,min(cap,self.target-time.monotonic(),self.adopt-time.monotonic()))
