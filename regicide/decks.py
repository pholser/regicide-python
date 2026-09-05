from __future__ import annotations

import random
from collections.abc import Iterable

from regicide.cards import NUMBER_RANKS, Card, Rank, Suit
from regicide.setup import jester_count


class TavernDeck:
    """The shared draw pile. Index 0 is the top (next card drawn)."""

    def __init__(self, cards: Iterable[Card] = ()) -> None:
        self._cards: list[Card] = list(cards)

    @property
    def size(self) -> int:
        return len(self._cards)

    @property
    def is_empty(self) -> bool:
        return not self._cards

    def draw(self) -> Card | None:
        """Draw the top card, or None if the deck is empty (no penalty)."""
        if not self._cards:
            return None
        return self._cards.pop(0)

    def place_under(self, cards: Iterable[Card]) -> None:
        """Place cards facedown on the bottom of the deck (the Hearts power)."""
        self._cards.extend(cards)

    @classmethod
    def build(cls, num_players: int, rng: random.Random) -> TavernDeck:
        cards = [Card(rank, suit) for rank in NUMBER_RANKS for suit in Suit]
        cards += [Card.animal_companion(suit) for suit in Suit]
        cards += [Card.jester() for _ in range(jester_count(num_players))]
        rng.shuffle(cards)
        return cls(cards)


class DiscardPile:
    """The shared discard pile."""

    def __init__(self, cards: Iterable[Card] = ()) -> None:
        self._cards: list[Card] = list(cards)

    @property
    def cards(self) -> tuple[Card, ...]:
        return tuple(self._cards)

    @property
    def size(self) -> int:
        return len(self._cards)

    @property
    def is_empty(self) -> bool:
        return not self._cards

    def add(self, card: Card) -> None:
        self._cards.append(card)

    def add_all(self, cards: Iterable[Card]) -> None:
        self._cards.extend(cards)

    def take_all(self) -> list[Card]:
        """Remove and return every card, emptying the pile.

        Used to implement the Hearts power: shuffle the returned cards,
        peel off some to go under the Tavern deck, and add the remainder
        back with ``add_all``.
        """
        taken = self._cards
        self._cards = []
        return taken


class CastleDeck:
    """The enemy queue: Jacks, then Queens, then Kings. Index 0 is next up."""

    def __init__(self, cards: Iterable[Card] = ()) -> None:
        self._cards: list[Card] = list(cards)

    @property
    def size(self) -> int:
        return len(self._cards)

    @property
    def is_empty(self) -> bool:
        return not self._cards

    def draw_next(self) -> Card | None:
        if not self._cards:
            return None
        return self._cards.pop(0)

    @classmethod
    def build(cls, rng: random.Random) -> CastleDeck:
        jacks = [Card(Rank.JACK, suit) for suit in Suit]
        queens = [Card(Rank.QUEEN, suit) for suit in Suit]
        kings = [Card(Rank.KING, suit) for suit in Suit]
        rng.shuffle(jacks)
        rng.shuffle(queens)
        rng.shuffle(kings)
        return cls(jacks + queens + kings)
