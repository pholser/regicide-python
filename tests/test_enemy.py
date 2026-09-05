import pytest

from regicide.cards import Card, Rank, Suit
from regicide.enemy import Enemy


class TestConstruction:
    def test_rejects_non_royal_card(self):
        with pytest.raises(ValueError):
            Enemy(Card(Rank.TWO, Suit.HEARTS))

    @pytest.mark.parametrize(
        "rank,attack,health",
        [
            (Rank.JACK, 10, 20),
            (Rank.QUEEN, 15, 30),
            (Rank.KING, 20, 40),
        ],
    )
    def test_stats_from_rank(self, rank, attack, health):
        enemy = Enemy(Card(rank, Suit.HEARTS))
        assert enemy.attack == attack
        assert enemy.health == health
        assert enemy.remaining_health == health
        assert not enemy.is_defeated


class TestDamage:
    def test_partial_damage_does_not_defeat(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        enemy.take_damage(9)
        assert enemy.remaining_health == 11
        assert not enemy.is_defeated

    def test_damage_accumulates_across_turns(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        enemy.take_damage(9)
        enemy.take_damage(12)
        assert enemy.is_defeated

    def test_exact_kill(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        enemy.take_damage(20)
        assert enemy.is_defeated
        assert enemy.is_exactly_defeated

    def test_overkill_is_not_exact(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        enemy.take_damage(25)
        assert enemy.is_defeated
        assert not enemy.is_exactly_defeated
        assert enemy.remaining_health == 0  # floors at zero, doesn't go negative

    def test_negative_damage_rejected(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        with pytest.raises(ValueError):
            enemy.take_damage(-1)


class TestShield:
    def test_shield_reduces_effective_attack(self):
        enemy = Enemy(Card(Rank.QUEEN, Suit.HEARTS))
        enemy.add_shield(6)
        assert enemy.effective_attack == 9

    def test_shield_is_cumulative(self):
        enemy = Enemy(Card(Rank.QUEEN, Suit.HEARTS))
        enemy.add_shield(6)
        enemy.add_shield(4)
        assert enemy.effective_attack == 5

    def test_shield_floors_effective_attack_at_zero(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        enemy.add_shield(999)
        assert enemy.effective_attack == 0

    def test_negative_shield_rejected(self):
        enemy = Enemy(Card(Rank.JACK, Suit.HEARTS))
        with pytest.raises(ValueError):
            enemy.add_shield(-1)


class TestSuitImmunity:
    def test_blocked_for_matching_suit_only(self):
        enemy = Enemy(Card(Rank.JACK, Suit.SPADES))
        assert enemy.is_suit_blocked(Suit.SPADES)
        assert not enemy.is_suit_blocked(Suit.HEARTS)
        assert not enemy.is_suit_blocked(Suit.CLUBS)
        assert not enemy.is_suit_blocked(Suit.DIAMONDS)

    def test_negate_immunity_removes_the_block(self):
        enemy = Enemy(Card(Rank.JACK, Suit.SPADES))
        enemy.negate_immunity()
        assert not enemy.is_suit_blocked(Suit.SPADES)
