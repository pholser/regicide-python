"""Baseline benchmark: how often simple policies win solo games.

Run with: python -m regicide.benchmark [--games N] [--start-seed N] [--policy NAME]
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from regicide.cards import Card
from regicide.enemy import Enemy
from regicide.game_state import GameOutcome, GameState
from regicide.legal_moves import legal_card_plays, legal_discards
from regicide.observer import NullObserver
from regicide.play import CardPlay
from regicide.player import Player


class RandomDecisions:
    """Picks uniformly among legal plays and discards, and never flips a Jester."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        return self._rng.choice(legal_card_plays(player))

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        return self._rng.choice(legal_discards(player, amount))

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        return False

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        return chooser


class GreedyDecisions:
    """Plays the highest-attack legal card and pays damage with the cheapest discard
    (least excess value, then fewest cards). Never flips a Jester."""

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        return max(legal_card_plays(player), key=lambda play: play.total_attack_value)

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        return min(
            legal_discards(player, amount),
            key=lambda cards: (sum(card.value for card in cards) - amount, len(cards)),
        )

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        return False

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        return chooser


POLICIES: dict[str, Callable[[random.Random], object]] = {
    "random": RandomDecisions,
    "greedy": lambda rng: GreedyDecisions(),
}


class _DefeatCounter(NullObserver):
    def __init__(self) -> None:
        self.enemies_defeated = 0

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None:
        self.enemies_defeated += 1


@dataclass(frozen=True)
class GameResult:
    seed: int
    policy: str
    won: bool
    enemies_defeated: int
    turns: int
    jesters_used: int


def play_game(seed: int, policy: str) -> GameResult:
    game_rng = random.Random(seed)
    state = GameState.new_game(1, game_rng)
    decisions = POLICIES[policy](random.Random(seed))
    counter = _DefeatCounter()
    turns = 0
    while not state.is_over:
        state.play_turn(decisions, game_rng, counter)
        turns += 1
    return GameResult(
        seed=seed,
        policy=policy,
        won=state.outcome is GameOutcome.WON,
        enemies_defeated=counter.enemies_defeated,
        turns=turns,
        jesters_used=state.solo_jesters.used,
    )


def summarize(policy: str, results: Sequence[GameResult], start_seed: int) -> str:
    games = len(results)
    wins = sum(result.won for result in results)
    mean_defeated = sum(result.enemies_defeated for result in results) / games
    mean_turns = sum(result.turns for result in results) / games
    return (
        f"{policy} policy, {games} games (seeds {start_seed}-{start_seed + games - 1}):\n"
        f"  wins {wins}/{games} ({wins / games:.1%})\n"
        f"  mean enemies defeated {mean_defeated:.2f} of 12\n"
        f"  mean turns {mean_turns:.1f}"
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Benchmark baseline policies on solo Regicide.")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--policy", choices=[*POLICIES, "all"], default="all")
    args = parser.parse_args(argv)

    names = list(POLICIES) if args.policy == "all" else [args.policy]
    seeds = range(args.start_seed, args.start_seed + args.games)
    for name in names:
        results = [play_game(seed, name) for seed in seeds]
        print(summarize(name, results, args.start_seed))


if __name__ == "__main__":
    main()
