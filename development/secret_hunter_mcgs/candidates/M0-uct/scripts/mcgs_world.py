"""Build an independent course-engine world exclusively from a legal observation.

No live Engine, opponent deck file, evaluation identity, or source RNG is accepted.
Unknown cards are hypotheses, never claimed to be inferred actual cards.
"""
from collections import Counter
import copy
import random

from hs_arena.engine import Engine
from hs_arena.deck import Deck
from hs_arena.cards import load
from hearthstone.enums import Zone


class Unsupported(ValueError):
    pass


def public_projection(state):
    """Exclude labels/presentation, preserve every decision-relevant visible field."""
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()
                    if k not in ('name', 'text', 'playable')}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    return clean({k: state.get(k) for k in ('turn', 'phase', 'you', 'opponent', 'choice')})


def hypotheses(state, rng, visible_only=False):
    """Class, copy limits, publicly spent cards and a broad cheap-card prior.

    The visible-only ablation uses expensive legal cards where possible; it also
    disables plays in the response policy. Unplayed cards are not negative evidence.
    """
    o = state['opponent']; cls = o['hero']['hero_class']; pool = load()
    seen = Counter(c['card_id'] for c in o['board'] + o.get('graveyard', []))
    if o.get('weapon'):
        seen[o['weapon']['card_id']] += 1
    shown = set(state.get('public_opponent_evidence', {}).get('shown_cards', []))
    choices = []
    for cid, c in pool.items():
        if c['card_class'] not in (cls, 'NEUTRAL'):
            continue
        limit = 1 if c['rarity'] == 'LEGENDARY' else 2
        for _ in range(max(0, limit-seen[cid])):
            # A deliberately weak, auditable prior. No proxy deck lists are used.
            weight = 1 / (1 + max(0, c['cost']-3))
            if c['card_class'] == cls:
                weight *= 1.5
            if cid in shown:
                weight *= 1.5
            choices.append((cid, weight))
    n = o.get('hand_size', 0)+o.get('deck_remaining', 0)
    if n > len(choices):
        raise Unsupported('opponent_card_count_exceeds_public_pool')
    result = []
    for _ in range(n):
        j = rng.choices(range(len(choices)), weights=[w for _, w in choices])[0]
        result.append(choices.pop(j)[0])
    return result[:o.get('hand_size', 0)], result[o.get('hand_size', 0):]


def build(state, seed=0, *, opponent_hand=None, opponent_deck=None):
    """Rehydrate visible stats; reject ambiguous effects rather than silently invent.

    Explicit opponent cards are an OFFLINE conditional-case interface only. The
    online adapter never supplies them. Entity IDs and board/secret order survive.
    """
    if state['phase'] not in ('main', 'choice'):
        raise Unsupported('phase')
    if state['opponent'].get('secrets_count'):
        raise Unsupported('unknown_enemy_secret')
    if any(m.get('windfury') for side in ('you', 'opponent') for m in state[side]['board']):
        raise Unsupported('ambiguous_windfury_attack_count')
    rng = random.Random(seed)
    y, o = state['you'], state['opponent']
    # A disposable legal deck initializes engine machinery. It contains no data
    # about either actual deck and is completely cleared before simulation.
    fillers = tuple(cid for cid,c in load().items() if c['card_class']=='NEUTRAL')[:30]
    e = Engine(Deck(y['hero']['hero_class'], fillers), Deck(o['hero']['hero_class'], fillers), seed)
    for i in (1, 2):
        assert e.step(i, {'type':'mulligan', 'replace':[]}).accepted
    for p in e._p:
        for c in list(p.hand)+list(p.deck)+list(p.field)+list(p.graveyard)+list(p.secrets):
            c.zone = Zone.SETASIDE
        p.choice = None
    p, q = e.player(1), e.player(2)
    e.game.current_player = p; e.game.turn = state['turn']
    # New hypothetical entities occupy a disjoint namespace. Public IDs remain exact.
    e.game.manager.counter = 100000
    adjust = []
    for pl, v in ((p, y), (q, o)):
        h = pl.hero; hv = v['hero']
        h.entity_id = hv['entity_id']; h.max_health = hv['max_health']
        h.damage = h.max_health-hv['health']; h.armor = hv['armor']
        h.frozen = hv.get('frozen', False)
        if hv.get('immune'):
            raise Unsupported('temporary_hero_immunity')
        h.num_attacks = 0 if hv.get('can_attack') else 1
        hp = v.get('hero_power')
        if hp:
            h.power.entity_id = hp['entity_id']; h.power.cost = hp['cost']
            # Inability caused only by mana is not evidence the power was spent.
            h.power.activations_this_turn = int(not hp.get('usable') and v['mana'] >= hp['cost']) if pl is p else 0
        pl.max_mana = v['max_mana']; pl.overload_locked = v.get('overloaded', 0)
        pl.overloaded = v.get('overload_next_turn', 0); pl.temp_mana = max(0, v['mana']-pl.max_mana)
        pl.used_mana = max(0, pl.max_mana-pl.overload_locked+pl.temp_mana-v['mana'])
        pl.fatigue_counter = v.get('fatigue', 0)
        for mv in v['board']:
            m = pl.card(mv['card_id'], zone=Zone.PLAY); m.entity_id = mv['entity_id']
            if mv.get('silenced'):
                m.silence()
            for attr, key in (('taunt','taunt'),('divine_shield','divine_shield'),('frozen','frozen'),
                              ('stealthed','stealth'),('charge','charge'),('poisonous','poisonous')):
                setattr(m, attr, bool(mv.get(key)))
            m.turns_in_play = 1
            m.num_attacks = 0 if (pl is q or mv.get('can_attack')) else 1
            adjust.append((m, mv))
        if v.get('weapon'):
            wv = v['weapon']; w = pl.card(wv['card_id'], zone=Zone.PLAY)
            w.entity_id = wv['entity_id']; w.atk = wv['attack']
            w.damage = w.max_health-wv['durability']
        # Public graveyard card identities affect death/resurrection effects.
        for c in v.get('graveyard', []):
            pl.card(c['card_id'], zone=Zone.GRAVEYARD)
        for sv in v.get('secrets', []):
            c = pl.card(sv['card_id'], zone=Zone.SECRET); c.entity_id = sv['entity_id']
    e.game.refresh_auras()
    for m, v in adjust:
        # Remove the currently active aura contribution from the stored base stat.
        m._atk += v['attack']-m.atk; m._max_health += v['max_health']-m.max_health
        m.damage = m.max_health-v['health']
        if bool(m.has_deathrattle) != bool(v.get('deathrattle')):
            raise Unsupported('unreconstructable_added_deathrattle')
    for hv in y['hand']:
        c = p.card(hv['card_id'], zone=Zone.HAND); c.entity_id = hv['entity_id']; c.cost = hv['cost']
    counts = y.get('deck_remaining_counts')
    if counts is None or sum(counts.values()) != y['deck_remaining']:
        raise Unsupported('missing_own_deck_counts')
    own_deck = list(Counter(counts).elements()); rng.shuffle(own_deck)
    for cid in own_deck:
        p.card(cid, zone=Zone.DECK)
    if opponent_hand is None:
        opponent_hand, opponent_deck = hypotheses(state, rng)
    elif opponent_deck is None:
        _, opponent_deck = hypotheses(state, rng)
    for cid in opponent_hand:
        q.card(cid, zone=Zone.HAND)
    for cid in opponent_deck:
        q.card(cid, zone=Zone.DECK)
    if state['phase'] == 'choice':
        source = (state.get('choice') or {}).get('source') or {}
        if source.get('card_id') != 'DS1_184':
            raise Unsupported('unsupported_choice_source')
        from hs_arena._vendor.fireplace.actions import GenericChoice
        template = next(a for a in state['legal_actions'] if a['type']=='choose')
        offered = []
        for v in template['options']:
            c = next((c for c in p.deck if c.id==v['card_id'] and c not in offered), None)
            if c is None:
                raise Unsupported('tracking_offer_not_in_public_deck')
            c.entity_id = v['entity_id']; offered.append(c)
        src = p.card('DS1_184'); src.entity_id = source.get('entity_id', src.entity_id)
        GenericChoice(p, offered).trigger(src)
    e.game.random.seed(rng.getrandbits(64))
    e._mark_seen(); e.events.clear()
    e._seen.update(c.entity_id for pl in e._p for c in pl.graveyard)
    # Verify the public projection and concrete legal actions before trusting it.
    actual = e.view(1)
    from actions import expand
    if {str(sorted(a.items())) for a in expand(actual)} != {str(sorted(a.items())) for a in expand(state)}:
        raise Unsupported('root_legal_action_mismatch')
    for side in ('you', 'opponent'):
        for old, new in zip(state[side]['board'], actual[side]['board']):
            if any(old.get(k) != new.get(k) for k in ('attack','health','max_health','taunt','divine_shield','deathrattle')):
                raise Unsupported('root_visible_stat_mismatch')
    return e


def clone(world, seed):
    result = copy.deepcopy(world)
    result.game.random.seed(seed)
    return result
