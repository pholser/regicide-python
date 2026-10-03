from __future__ import annotations

from itertools import combinations

from regicide.actions import YIELD, Action
from regicide.cards import Card
from regicide.game_state import GameState
from regicide.play import CardPlay, InvalidPlay
from regicide.player import Player


def legal_card_plays(player: Player) -> tuple[CardPlay, ...]:
    """Return every legal Step 1 card play available from the player hand."""
    hand = player.hand.cards
    plays: list[CardPlay] = []

    for size in range(1, min(4, len(hand)) + 1):
        for cards in combinations(hand, size):
            try:
                plays.append(CardPlay.create(*cards))
            except InvalidPlay:
                pass

    return tuple(plays)


def legal_actions(player: Player, state: GameState) -> tuple[Action, ...]:
    """Return every legal Step 1 action available to player."""
    actions: list[Action] = list(legal_card_plays(player))
    if player is state.current_player and state.turn_order.can_yield():
        actions.append(YIELD)
    return tuple(actions)


def legal_discards(player: Player, amount: int) -> tuple[tuple[Card, ...], ...]:
    """Return every subset of the hand that can satisfy amount damage."""
    hand = player.hand.cards
    discards: list[tuple[Card, ...]] = []

    for size in range(1, len(hand) + 1):
        for cards in combinations(hand, size):
            if sum(card.value for card in cards) >= amount:
                discards.append(cards)

    return tuple(discards)
