from __future__ import annotations

import random
from collections.abc import Iterable

from regicide.cards import NUMBER_RANKS, Card, Rank, Suit

# Plain Enum members hash by object identity, so iterating a *set* of them
# (like NUMBER_RANKS) is not stable across process runs -- that would silently
# break `--seed`-based reproducibility. Iterating the Rank class itself is
# guaranteed to follow definition order, so build from that instead.
_NUMBER_RANKS_IN_ORDER = tuple(rank for rank in Rank if rank in NUMBER_RANKS)
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

    def place_on_top(self, cards: Iterable[Card]) -> None:
        """Place cards facedown on top of the deck (an exactly-defeated enemy)."""
        self._cards[0:0] = list(cards)

    @classmethod
    def build(cls, num_players: int, rng: random.Random) -> TavernDeck:
        cards = [Card(rank, suit) for rank in _NUMBER_RANKS_IN_ORDER for suit in Suit]
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
        """Remove and return every card, emptying the pile."""
        taken = self._cards
        self._cards = []
        return taken

    def heal_into(self, tavern: TavernDeck, amount: int, rng: random.Random) -> int:
        """The Hearts power: shuffle this pile, bury ``amount`` cards facedown
        under the Tavern deck, and return the rest to this pile. Returns the
        number of cards actually buried (may be fewer than ``amount`` if this
        pile didn't have that many)."""
        pool = self.take_all()
        rng.shuffle(pool)
        to_bury = pool[:amount]
        tavern.place_under(to_bury)
        self.add_all(pool[amount:])
        return len(to_bury)


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
