from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"


class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ANIMAL_COMPANION = "AC"
    JESTER = "Jester"

    @property
    def attack_value(self) -> int:
        return _ATTACK_VALUES[self]


_ATTACK_VALUES: dict[Rank, int] = {
    Rank.TWO: 2,
    Rank.THREE: 3,
    Rank.FOUR: 4,
    Rank.FIVE: 5,
    Rank.SIX: 6,
    Rank.SEVEN: 7,
    Rank.EIGHT: 8,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 10,
    Rank.QUEEN: 15,
    Rank.KING: 20,
    Rank.ANIMAL_COMPANION: 1,
    Rank.JESTER: 0,
}

NUMBER_RANKS = frozenset(
    {
        Rank.TWO,
        Rank.THREE,
        Rank.FOUR,
        Rank.FIVE,
        Rank.SIX,
        Rank.SEVEN,
        Rank.EIGHT,
        Rank.NINE,
        Rank.TEN,
    }
)
ROYAL_RANKS = frozenset({Rank.JACK, Rank.QUEEN, Rank.KING})


@dataclass(frozen=True)
class Card:
    """An immutable Regicide playing card.

    The Jester is suitless; every other rank must carry a suit.
    """

    rank: Rank
    suit: Suit | None = None

    def __post_init__(self) -> None:
        if self.rank is Rank.JESTER:
            if self.suit is not None:
                raise ValueError("Jester cards cannot have a suit")
        elif self.suit is None:
            raise ValueError(f"{self.rank} cards must have a suit")

    @classmethod
    def jester(cls) -> Card:
        return cls(Rank.JESTER)

    @classmethod
    def animal_companion(cls, suit: Suit) -> Card:
        return cls(Rank.ANIMAL_COMPANION, suit)

    @property
    def value(self) -> int:
        return self.rank.attack_value

    @property
    def is_jester(self) -> bool:
        return self.rank is Rank.JESTER

    @property
    def is_animal_companion(self) -> bool:
        return self.rank is Rank.ANIMAL_COMPANION

    @property
    def is_royal(self) -> bool:
        return self.rank in ROYAL_RANKS

    @property
    def is_number(self) -> bool:
        return self.rank in NUMBER_RANKS

    def __str__(self) -> str:
        if self.is_jester:
            return "Jester"
        return f"{self.rank.value}{self.suit.value[0]}"
