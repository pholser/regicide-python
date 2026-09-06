from __future__ import annotations

from collections.abc import Iterable, Iterator

from regicide.cards import Card


class HandError(Exception):
    """Base class for Hand invariant violations."""


class HandFullError(HandError):
    """Raised when adding a card would exceed the hand's max size."""


class CardNotInHand(HandError):
    """Raised when removing a card that isn't present in the hand."""


class Hand:
    """A player's held cards, bounded by a fixed max size.

    ``add``/``remove`` are the only ways to mutate the hand, so the max-size
    invariant can't be bypassed by reaching into the card list directly.
    """

    def __init__(self, max_size: int, cards: Iterable[Card] = ()) -> None:
        self.max_size = max_size
        self._cards: list[Card] = list(cards)
        if len(self._cards) > self.max_size:
            raise ValueError(
                f"cannot hold {len(self._cards)} cards with a max size of {max_size}"
            )

    @property
    def cards(self) -> tuple[Card, ...]:
        return tuple(self._cards)

    @property
    def size(self) -> int:
        return len(self._cards)

    @property
    def is_full(self) -> bool:
        return self.size >= self.max_size

    @property
    def is_empty(self) -> bool:
        return not self._cards

    @property
    def total_value(self) -> int:
        return sum(card.value for card in self._cards)

    def add(self, card: Card) -> None:
        if self.is_full:
            raise HandFullError(f"hand already at max size ({self.max_size})")
        self._cards.append(card)

    def remove(self, card: Card) -> None:
        try:
            self._cards.remove(card)
        except ValueError:
            raise CardNotInHand(f"{card} is not in hand") from None

    def remove_all(self, cards: Iterable[Card]) -> None:
        """Remove every card in ``cards``, or none at all.

        Validates that all of them are present before removing any, so a
        bad request can't leave the hand missing only some of the cards.
        """
        cards = list(cards)
        remaining = list(self._cards)
        for card in cards:
            try:
                remaining.remove(card)
            except ValueError:
                raise CardNotInHand(f"{card} is not in hand") from None
        for card in cards:
            self._cards.remove(card)

    def __len__(self) -> int:
        return self.size

    def __contains__(self, card: object) -> bool:
        return card in self._cards

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)
