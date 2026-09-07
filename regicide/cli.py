"""A simple terminal client for playing Regicide end-to-end.

Run with: python -m regicide.cli [--players N] [--seed N]
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence

from regicide.actions import YIELD, Action
from regicide.cards import Card, Rank, Suit
from regicide.enemy import Enemy
from regicide.game_state import GameOutcome, GameState
from regicide.hand import CardNotInHand
from regicide.play import CardPlay, InvalidPlay
from regicide.player import InsufficientDiscard, Player
from regicide.turn_order import IllegalAction

_RANK_LABELS = {
    Rank.TWO: "2",
    Rank.THREE: "3",
    Rank.FOUR: "4",
    Rank.FIVE: "5",
    Rank.SIX: "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
    Rank.ANIMAL_COMPANION: "A",
}

_SUIT_SYMBOLS = {
    Suit.HEARTS: "♥",  # ♥
    Suit.DIAMONDS: "♦",  # ♦
    Suit.CLUBS: "♣",  # ♣
    Suit.SPADES: "♠",  # ♠
}


def describe_card(card: Card) -> str:
    if card.is_jester:
        return "Jester"
    return f"{_RANK_LABELS[card.rank]}{_SUIT_SYMBOLS[card.suit]}"


class CLIDecisions:
    """A Decisions and TurnObserver implementation for a human at the
    terminal. In a multiplayer game every player shares this same terminal
    (hot-seat).
    """

    def choose_action(self, player: Player, state: GameState) -> Action:
        self._print_status(state)
        print(f"\n{player.name}'s turn. Your hand:")
        self._print_hand(player)
        while True:
            raw = input("Play cards by number (e.g. '2 4'), or 'yield': ").strip()
            if raw.lower() in ("yield", "y"):
                if not state.turn_order.can_yield():
                    print("You can't yield: every other player yielded last turn. Play a card.")
                    continue
                return YIELD
            indices = self._parse_indices(raw)
            if indices is None:
                continue
            cards = self._cards_by_index(player, indices)
            if cards is None:
                continue
            try:
                return CardPlay.create(*cards)
            except InvalidPlay as error:
                print(f"Illegal play: {error}")

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        enemy = state.enemy
        print(
            f"\n{describe_card(enemy.card)} attacks {player.name} for {amount}! "
            "Choose cards to discard."
        )
        self._print_hand(player)
        while True:
            raw = input(f"Discard cards totaling >= {amount} (or 'all'): ").strip()
            if raw.lower() == "all":
                return player.hand.cards
            indices = self._parse_indices(raw)
            if indices is None:
                continue
            cards = self._cards_by_index(player, indices)
            if cards is None:
                continue
            total = sum(card.value for card in cards)
            if total < amount:
                print(f"That only totals {total}; need at least {amount}.")
                continue
            return tuple(cards)

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        print(f"\n{chooser.name} played the Jester! Choose who goes next:")
        for i, player in enumerate(state.players, start=1):
            marker = " (you)" if player is chooser else ""
            print(f"  {i}: {player.name}{marker}")
        while True:
            raw = input("Choice: ").strip()
            index = self._parse_index(raw, len(state.players))
            if index is None:
                continue
            return state.players[index - 1]

    # -- TurnObserver -----------------------------------------------------

    def on_yield(self, player: Player) -> None:
        print(f"\n{player.name} yields.")

    def on_play(self, player: Player, play: CardPlay) -> None:
        cards = ", ".join(describe_card(card) for card in play.cards)
        print(f"\n{player.name} plays {cards} (attack value {play.total_attack_value}).")

    def on_hearts(self, healed: int, blocked: bool) -> None:
        if blocked:
            print("Hearts power blocked: this enemy is immune.")
        elif healed:
            print(f"Healed {healed} card(s) from the discard pile back into the Tavern deck.")
        else:
            print("No cards in the discard pile to heal.")

    def on_diamonds(self, drawn: int, blocked: bool) -> None:
        if blocked:
            print("Diamonds power blocked: this enemy is immune.")
        elif drawn:
            print(f"Drew {drawn} card(s) from the Tavern deck.")
        else:
            print("No cards could be drawn (Tavern deck empty or hands full).")

    def on_damage_dealt(self, enemy: Enemy, amount: int, doubled: bool) -> None:
        note = " (doubled by Clubs)" if doubled else ""
        print(
            f"Dealt {amount} damage{note} to {describe_card(enemy.card)}. "
            f"{enemy.remaining_health}/{enemy.health} HP remaining."
        )

    def on_shield_added(self, enemy: Enemy, amount: int) -> None:
        if amount:
            print(f"Spades reduce this enemy's attack by {amount} (shield now {enemy.shield}).")
        else:
            print("Spades power blocked: this enemy is immune.")

    def on_jester_negated_immunity(self, enemy: Enemy) -> None:
        print(f"The Jester negates {describe_card(enemy.card)}'s immunity!")

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None:
        if exact:
            print(f"{describe_card(enemy.card)} is defeated (exact kill)! It goes facedown atop the Tavern deck.")
        else:
            print(f"{describe_card(enemy.card)} is defeated!")

    def on_enemy_revealed(self, enemy: Enemy) -> None:
        print(f"A new enemy is revealed: {describe_card(enemy.card)} (HP {enemy.health}, Attack {enemy.attack}).")

    def on_player_suffered(self, player: Player, amount: int, discarded: tuple[Card, ...]) -> None:
        cards = ", ".join(describe_card(card) for card in discarded)
        print(f"{player.name} discards {cards} to cover {amount} damage.")

    # -- shared helpers -----------------------------------------------------

    def _print_status(self, state: GameState) -> None:
        enemy = state.enemy
        print("\n" + "=" * 60)
        print(
            f"Enemy: {describe_card(enemy.card)}  "
            f"HP: {enemy.remaining_health}/{enemy.health}  "
            f"Attack: {enemy.effective_attack} (base {enemy.attack}, shield {enemy.shield})"
        )
        print(f"Tavern deck: {state.tavern.size}   Discard pile: {state.discard.size}")

    def _print_hand(self, player: Player) -> None:
        for i, card in enumerate(player.hand.cards, start=1):
            print(f"  {i}: {describe_card(card)}")

    def _parse_indices(self, raw: str) -> list[int] | None:
        if not raw:
            print("Enter at least one card number.")
            return None
        try:
            indices = [int(token) for token in raw.split()]
        except ValueError:
            print("Enter numbers separated by spaces.")
            return None
        if len(set(indices)) != len(indices):
            print("Pick each card only once.")
            return None
        return indices

    def _parse_index(self, raw: str, count: int) -> int | None:
        try:
            index = int(raw)
        except ValueError:
            print("Enter a number.")
            return None
        if not (1 <= index <= count):
            print(f"Enter a number from 1 to {count}.")
            return None
        return index

    def _cards_by_index(self, player: Player, indices: list[int]) -> list[Card] | None:
        hand = player.hand.cards
        cards = []
        for i in indices:
            if not (1 <= i <= len(hand)):
                print(f"{i} is not a valid card number.")
                return None
            cards.append(hand[i - 1])
        return cards


def _prompt_num_players() -> int:
    while True:
        raw = input("Number of players (1-4): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 4:
            return int(raw)
        print("Please enter a number from 1 to 4.")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Play Regicide from the command line.")
    parser.add_argument("--players", type=int, choices=[1, 2, 3, 4], help="number of players")
    parser.add_argument("--seed", type=int, help="random seed, for a reproducible game")
    args = parser.parse_args(argv)

    print("Welcome to Regicide!")
    num_players = args.players if args.players is not None else _prompt_num_players()
    rng = random.Random(args.seed)

    state = GameState.new_game(num_players, rng)
    decisions = CLIDecisions()

    try:
        while not state.is_over:
            state.play_turn(decisions, rng, observer=decisions)
    except (IllegalAction, InvalidPlay, CardNotInHand, InsufficientDiscard) as error:
        print(f"\nInternal error, aborting: {error}")
        return

    print("\n" + "=" * 60)
    if state.outcome is GameOutcome.WON:
        print("Victory! All twelve monarchs have been defeated.")
    else:
        print("Defeat... the corruption has consumed the realm.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGame aborted.")
