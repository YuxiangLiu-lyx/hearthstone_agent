"""UCD graph statistics and empirical chance sampling, independently implemented.

Choe and Kim (2019), Eq. 3, Algorithm 1, III-E; see docs/SOURCES.md.
Edge visits and node payoff visits are deliberately different counters.
"""
from dataclasses import dataclass, field
import math


@dataclass(eq=False)
class Node:
    key: str
    visits: int = 0
    total: int = 0
    reward: float = 0.
    incoming: list = field(default_factory=list)
    outgoing: dict = field(default_factory=dict)

    @property
    def mean(self):
        return self.reward/self.visits if self.visits else .5


@dataclass(eq=False)
class Edge:
    parent: Node
    child: Node
    action: object
    visits: int = 0
    samples: int = 1

    def value(self, c):
        if not self.visits:
            return float('inf')
        return self.child.mean+c*math.sqrt(2*math.log(max(1,self.parent.total))/self.visits)


class Graph:
    def __init__(self, mode='ucd', d1=2, d2=1):
        self.nodes={};self.mode=mode;self.d1=d1;self.d2=d2
        self.transpositions=0;self.offpath_updates=0

    def node(self, key):
        if key not in self.nodes:
            self.nodes[key]=Node(key)
        return self.nodes[key]

    def connect(self, parent, child, action):
        key=str(action)+'|'+child.key
        if key not in parent.outgoing:
            edge=Edge(parent,child,action);parent.outgoing[key]=edge
            if child.incoming:self.transpositions+=1
            child.incoming.append(edge)
        return parent.outgoing[key]

    def backup(self, path, reward):
        """On-path update plus finite-depth alternate-parent propagation.

        Path contains edges; graph must be acyclic. Exclude the incoming edge
        traversed to this node, exactly as Node.UCDUpdate does in the source.
        """
        if not path:return
        def off(edge,d1,d2):
            if d1<=1 and d2<=0:return
            self.offpath_updates+=1
            if d1>1:
                edge.parent.reward+=reward;edge.parent.visits+=1
            if d2>0:
                edge.visits+=1;edge.parent.total+=1
            for previous in edge.parent.incoming:
                off(previous,d1-1,d2-1)
        nodes=[path[0].parent]+[e.child for e in path]
        for index,node in enumerate(nodes):
            node.reward+=reward;node.visits+=1;node.total+=1
            incoming=path[index-1] if index else None
            if self.mode=='ucd':
                for edge in node.incoming:
                    if edge is not incoming:off(edge,self.d1,self.d2)
        for edge in path:edge.visits+=1


class Chance:
    def __init__(self):
        self.outcomes={};self.count=0;self.visits=0

    def add(self,key,payload):
        self.count+=1
        if key in self.outcomes:
            self.outcomes[key]['count']+=1
        else:
            self.outcomes[key]={'count':1,'payload':payload}

    def sample(self,rng):
        keys=list(self.outcomes)
        k=rng.choices(keys,weights=[self.outcomes[k]['count'] for k in keys])[0]
        return k,self.outcomes[k]['payload']

    def width(self,cfg,large_chance_depth=0):
        if cfg.get('chance','dpw')=='fixed':return max(1,cfg.get('width',4))
        raw=cfg.get('dpw_c',.5)*max(1,self.visits)**cfg.get('alpha',.6)
        eta=cfg.get('eta',2.)**large_chance_depth
        if cfg.get('rounding','source')=='paper':return max(1,math.floor(raw/eta))
        # C# Math.Ceiling followed by Convert.ToInt32 uses ties-to-even rounding.
        return max(1,round(math.ceil(raw)/eta))
