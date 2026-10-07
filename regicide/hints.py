"""Hints for a human player: the play a policy would make, and what that play does.

The Tavern order is unknown to the player, so each hint simulates the turn from a
reshuffled Tavern, the same way the policies do.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

from regicide.benchmark import DiamondsTimingDecisions, ForcedFirstPlay, terminal_value
from regicide.enemy import Enemy
from regicide.features import extract
from regicide.game_state import GameState
from regicide.observer import NullObserver
from regicide.play import CardPlay
from regicide.value_model import LinearValueModel


class _TurnFacts(NullObserver):
    def __init__(self) -> None:
        self.damage = 0
        self.defeats = 0
        self.shield = 0

    def on_damage_dealt(self, enemy: Enemy, amount: int, doubled: bool) -> None:
        self.damage += amount

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None:
        self.defeats += 1

    def on_shield_added(self, enemy: Enemy, amount: int) -> None:
        self.shield += amount


@dataclass(frozen=True)
class Hint:
    policy_name: str
    play: CardPlay
    damage: int
    defeats: int
    shield: int
    hand_after: int
    game_over: bool
    model_estimate: float


def recommend(
    policy_name: str,
    policy: object,
    state: GameState,
    rng: random.Random,
    model: LinearValueModel,
) -> Hint:
    candidate = copy.deepcopy(state)
    play = policy.choose_action(candidate.current_player, candidate)

    sim = copy.deepcopy(state)
    sim.tavern.shuffle(rng)
    facts = _TurnFacts()
    sim.play_turn(ForcedFirstPlay(play, DiamondsTimingDecisions()), rng, facts)

    game_over = sim.is_over
    if game_over:
        hand_after = 0
        estimate = terminal_value(sim)
    else:
        hand_after = sim.current_player.hand.total_value
        estimate = model.predict(extract(sim.current_player, sim))
    return Hint(
        policy_name=policy_name,
        play=play,
        damage=facts.damage,
        defeats=facts.defeats,
        shield=facts.shield,
        hand_after=hand_after,
        game_over=game_over,
        model_estimate=estimate,
    )
