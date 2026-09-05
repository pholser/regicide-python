from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from regicide.cards import Card, Suit


class InvalidPlay(ValueError):
    """Raised when a set of cards does not form a legal Step 1 play."""


class PlayKind(Enum):
    SINGLE = "single"
    ANIMAL_COMPANION_PAIR = "animal_companion_pair"
    COMBO = "combo"
    JESTER = "jester"


@dataclass(frozen=True)
class CardPlay:
    """A validated set of cards played together against the enemy in Step 1.

    Construction enforces every combinability rule (Jester-alone, Animal
    Companion pairing, same-rank combos totalling 10 or less), so any
    ``CardPlay`` instance that exists is guaranteed legal.
    """

    cards: tuple[Card, ...]

    def __post_init__(self) -> None:
        _validate(self.cards)

    @classmethod
    def create(cls, *cards: Card) -> CardPlay:
        return cls(tuple(cards))

    @property
    def kind(self) -> PlayKind:
        if self.cards[0].is_jester:
            return PlayKind.JESTER
        if len(self.cards) == 1:
            return PlayKind.SINGLE
        if any(card.is_animal_companion for card in self.cards):
            return PlayKind.ANIMAL_COMPANION_PAIR
        return PlayKind.COMBO

    @property
    def total_attack_value(self) -> int:
        return sum(card.value for card in self.cards)

    @property
    def active_suits(self) -> frozenset[Suit]:
        """Suits whose powers trigger, applied at most once each.

        A set naturally captures the rule that pairing an Animal Companion
        with a card of the same suit only triggers that suit's power once.
        """
        return frozenset(card.suit for card in self.cards if card.suit is not None)

    @property
    def is_jester(self) -> bool:
        return self.kind is PlayKind.JESTER


def _validate(cards: tuple[Card, ...]) -> None:
    if not cards:
        raise InvalidPlay("a play must contain at least one card")

    if any(card.is_jester for card in cards):
        if len(cards) != 1:
            raise InvalidPlay("the Jester must be played alone")
        return

    if len(cards) == 1:
        return

    if len(cards) > 4:
        raise InvalidPlay("a play may contain at most 4 cards")

    if any(card.is_animal_companion for card in cards):
        if len(cards) != 2:
            raise InvalidPlay(
                "an Animal Companion may only be paired with exactly one other card"
            )
        return

    ranks = {card.rank for card in cards}
    if len(ranks) != 1:
        raise InvalidPlay("combo cards must all share the same rank")

    (rank,) = ranks
    total = rank.attack_value * len(cards)
    if total > 10:
        raise InvalidPlay(f"combo attack total must be 10 or less (got {total})")
