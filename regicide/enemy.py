from __future__ import annotations

from regicide.cards import Card, Rank, ROYAL_RANKS, Suit
from regicide.play import CardPlay

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

    def resolve_play(self, play: CardPlay) -> bool:
        """React to being attacked by ``play`` (Step 3, plus Spades' Step 4
        shield since nothing observes it in between): apply a Spades shield,
        double the damage for Clubs, take the damage, and report whether
        that defeated this enemy. Suits this enemy is immune to are ignored,
        matching that the raw attack value still counts toward damage.
        """
        if Suit.SPADES in play.active_suits and not self.is_suit_blocked(Suit.SPADES):
            self.add_shield(play.total_attack_value)

        amount = play.total_attack_value
        if Suit.CLUBS in play.active_suits and not self.is_suit_blocked(Suit.CLUBS):
            amount *= 2
        self.take_damage(amount)

        return self.is_defeated
