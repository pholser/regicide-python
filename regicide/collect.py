"""Collect player-visible features and game outcomes from seeded solo games.

Run with: python -m regicide.collect --policy NAME [--games N] [--start-seed N] --out FILE.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from collections.abc import Sequence
from dataclasses import dataclass

from regicide.benchmark import POLICIES, DefeatCounter
from regicide.cards import Card
from regicide.features import FEATURE_NAMES, extract
from regicide.game_state import GameOutcome, GameState
from regicide.play import CardPlay
from regicide.player import Player


class _Recording:
    """Delegates every decision to a policy, recording features before each Step 1 play."""

    def __init__(self, policy: object, rows: list[tuple[float, ...]]) -> None:
        self._policy = policy
        self._rows = rows

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        self._rows.append(extract(player, state))
        return self._policy.choose_action(player, state)

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        return self._policy.choose_discard(player, amount, state)

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        return self._policy.choose_use_jester(player, state)

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        return self._policy.choose_next_player(chooser, state)


@dataclass(frozen=True)
class Row:
    seed: int
    decision: int
    won: bool
    enemies_defeated: int
    features: tuple[float, ...]


def collect_game(policy_name: str, seed: int) -> list[Row]:
    game_rng = random.Random(seed)
    state = GameState.new_game(1, game_rng)
    feature_rows: list[tuple[float, ...]] = []
    decisions = _Recording(POLICIES[policy_name](random.Random(seed)), feature_rows)
    counter = DefeatCounter()
    while not state.is_over:
        state.play_turn(decisions, game_rng, counter)
    won = state.outcome is GameOutcome.WON
    return [
        Row(seed, decision, won, counter.enemies_defeated, features)
        for decision, features in enumerate(feature_rows)
    ]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Collect features and outcomes from solo games.")
    parser.add_argument("--policy", choices=list(POLICIES), required=True)
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    seeds = range(args.start_seed, args.start_seed + args.games)
    with open(args.out, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "decision", "won", "enemies_defeated", *FEATURE_NAMES])
        total = 0
        for seed in seeds:
            for row in collect_game(args.policy, seed):
                writer.writerow(
                    [row.seed, row.decision, int(row.won), row.enemies_defeated, *row.features]
                )
                total += 1
    print(f"wrote {total} rows from {args.games} games to {args.out}")


if __name__ == "__main__":
    main()
