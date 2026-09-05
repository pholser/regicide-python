from __future__ import annotations

from regicide.cards import Card, Rank, ROYAL_RANKS, Suit

_ENEMY_STATS: dict[Rank, tuple[int, int]] = {
    # rank -> (attack, health)
    Rank.JACK: (10, 20),
    Rank.QUEEN: (15, 30),
    Rank.KING: (20, 40),
}


class Enemy:
    """The current face-up Castle card and its battle state."""

    def __init__(self, card: Card) -> None:
        if card.rank not in ROYAL_RANKS:
            raise ValueError(f"{card.rank} cannot be an enemy")
        self.card = card
        self.attack, self.health = _ENEMY_STATS[card.rank]
        self.damage_taken = 0
        self.shield = 0
        self.immunity_negated = False

    @property
    def remaining_health(self) -> int:
        return max(0, self.health - self.damage_taken)

    @property
    def is_defeated(self) -> bool:
        return self.damage_taken >= self.health

    @property
    def is_exactly_defeated(self) -> bool:
        """True when damage dealt lands exactly on health (facedown-on-Tavern-deck case)."""
        return self.damage_taken == self.health

    @property
    def effective_attack(self) -> int:
        return max(0, self.attack - self.shield)

    def is_suit_blocked(self, suit: Suit) -> bool:
        return suit is self.card.suit and not self.immunity_negated

    def take_damage(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("damage cannot be negative")
        self.damage_taken += amount

    def add_shield(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("shield cannot be negative")
        self.shield += amount

    def negate_immunity(self) -> None:
        self.immunity_negated = True
