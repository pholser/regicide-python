"""Baseline benchmark: how often simple policies win solo games.

Run with: python -m regicide.benchmark [--games N] [--start-seed N] [--policy NAME]
"""

from __future__ import annotations

import argparse
import copy
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from regicide.cards import Card, Suit
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


class GreedyRescueDecisions(GreedyDecisions):
    """Greedy, but flips a Jester whenever the hand can't cover the enemy's attack."""

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        return player.hand.total_value < state.enemy.effective_attack


class ShieldFirstDecisions(GreedyRescueDecisions):
    """Greedy rescue, preferring the highest Spades play while the enemy isn't immune to Spades."""

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        return self._pick(state, legal_card_plays(player))

    def _pick(self, state: GameState, plays: Sequence[CardPlay]) -> CardPlay:
        if not state.enemy.is_suit_blocked(Suit.SPADES):
            shields = [play for play in plays if Suit.SPADES in play.active_suits]
            if shields:
                return max(shields, key=lambda play: play.total_attack_value)
        return max(plays, key=lambda play: play.total_attack_value)


class DiamondsTimingDecisions(ShieldFirstDecisions):
    """Shield-first, but keeps Diamonds plays for when the hand is low.

    With a hand worth at least two of the enemy's hits, Diamonds plays are held back;
    below that, Diamonds plays are preferred.
    """

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        plays = legal_card_plays(player)
        diamonds = [play for play in plays if Suit.DIAMONDS in play.active_suits]
        others = [play for play in plays if Suit.DIAMONDS not in play.active_suits]
        low = player.hand.total_value < 2 * state.enemy.effective_attack
        preferred = diamonds if low else others
        return self._pick(state, preferred or plays)


KEEP_VALUE = {Suit.SPADES: 2, Suit.DIAMONDS: 1, Suit.CLUBS: 0, Suit.HEARTS: 0}


class SuitAwareDecisions(DiamondsTimingDecisions):
    """Diamonds timing, but among equally cheap covers keeps Spades and Diamonds."""

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        return min(
            legal_discards(player, amount),
            key=lambda cards: (
                sum(card.value for card in cards) - amount,
                sum(KEEP_VALUE.get(card.suit, 0) for card in cards),
                len(cards),
            ),
        )


ROLLOUTS_PER_PLAY = 8


class _ForcedFirstPlay:
    """Plays a candidate as the first Step 1 action, then defers to a fallback policy.

    The Jester offer that precedes Step 1 has already been decided by the real game,
    so it's declined here so the candidate still matches the hand.
    """

    def __init__(self, first: CardPlay, fallback: DiamondsTimingDecisions) -> None:
        self._first: CardPlay | None = first
        self._fallback = fallback
        self._offered_jester = False

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        if self._first is not None:
            first, self._first = self._first, None
            return first
        return self._fallback.choose_action(player, state)

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        return self._fallback.choose_discard(player, amount, state)

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        if not self._offered_jester:
            self._offered_jester = True
            return False
        return self._fallback.choose_use_jester(player, state)

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        return self._fallback.choose_next_player(chooser, state)


class LookaheadDecisions(DiamondsTimingDecisions):
    """Scores each legal play by complete rollouts from the resulting state.

    Each rollout reshuffles the unseen Tavern and plays the rest of the game with the
    diamonds-timing policy. The play with the best win rate wins, ties go to mean
    enemies defeated.
    """

    def __init__(
        self,
        rng: random.Random,
        rollouts: int = ROLLOUTS_PER_PLAY,
        rollout_policy: DiamondsTimingDecisions | None = None,
    ) -> None:
        self._rng = rng
        self._rollouts = rollouts
        self._rollout_policy = rollout_policy or DiamondsTimingDecisions()

    def choose_action(self, player: Player, state: GameState) -> CardPlay:
        best_play: CardPlay | None = None
        best_key: tuple[float, float] | None = None
        for play in legal_card_plays(player):
            key = self._evaluate(state, play)
            if best_key is None or key > best_key:
                best_play, best_key = play, key
        assert best_play is not None
        return best_play

    def _evaluate(self, state: GameState, play: CardPlay) -> tuple[float, float]:
        wins = 0
        defeated = 0
        for _ in range(self._rollouts):
            sim = copy.deepcopy(state)
            sim.tavern.shuffle(self._rng)
            decisions = _ForcedFirstPlay(play, self._rollout_policy)
            counter = _DefeatCounter()
            while not sim.is_over:
                sim.play_turn(decisions, self._rng, counter)
            wins += sim.outcome is GameOutcome.WON
            defeated += counter.enemies_defeated
        return wins / self._rollouts, defeated / self._rollouts


POLICIES: dict[str, Callable[[random.Random], object]] = {
    "random": RandomDecisions,
    "greedy": lambda rng: GreedyDecisions(),
    "greedy_rescue": lambda rng: GreedyRescueDecisions(),
    "shield_first": lambda rng: ShieldFirstDecisions(),
    "diamonds_timing": lambda rng: DiamondsTimingDecisions(),
    "lookahead": lambda rng: LookaheadDecisions(rng),
    "lookahead_suit_aware": lambda rng: LookaheadDecisions(
        rng, rollout_policy=SuitAwareDecisions()
    ),
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
