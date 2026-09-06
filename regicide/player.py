from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from regicide.cards import Card
from regicide.hand import Hand
from regicide.play import CardPlay


class InsufficientDiscard(ValueError):
    """Raised when a chosen discard doesn't total enough to satisfy an attack."""


@dataclass(eq=False)
class Player:
    """A seat at the table. Turn order/seating is managed by whatever holds
    the list of Players, not by Player itself.

    Equality/hashing is identity-based (eq=False), since two distinct seats
    could otherwise share a name and an equal-by-value hand; turn tracking
    needs to tell them apart regardless.
    """

    name: str
    hand: Hand

    def play(self, play: CardPlay) -> None:
        """Play (already-validated) cards from hand. Raises CardNotInHand
        if any of them aren't actually held."""
        self.hand.remove_all(play.cards)

    def can_survive(self, amount: int) -> bool:
        return self.hand.total_value >= amount

    def discard(self, cards: Iterable[Card], amount: int) -> tuple[Card, ...]:
        """Discard ``cards`` from hand to satisfy an attack of ``amount``.

        Raises InsufficientDiscard if the chosen cards don't total enough,
        or CardNotInHand if any of them aren't actually held.
        """
        cards = tuple(cards)
        total = sum(card.value for card in cards)
        if total < amount:
            raise InsufficientDiscard(
                f"discarded cards total {total}, need at least {amount}"
            )
        self.hand.remove_all(cards)
        return cards
