import pytest

from regicide.cards import Card, Rank, Suit


class TestRankAttackValue:
    @pytest.mark.parametrize(
        "rank,expected",
        [
            (Rank.TWO, 2),
            (Rank.THREE, 3),
            (Rank.FOUR, 4),
            (Rank.FIVE, 5),
            (Rank.SIX, 6),
            (Rank.SEVEN, 7),
            (Rank.EIGHT, 8),
            (Rank.NINE, 9),
            (Rank.TEN, 10),
            (Rank.JACK, 10),
            (Rank.QUEEN, 15),
            (Rank.KING, 20),
            (Rank.ANIMAL_COMPANION, 1),
            (Rank.JESTER, 0),
        ],
    )
    def test_attack_value(self, rank, expected):
        assert rank.attack_value == expected


class TestCardConstruction:
    def test_number_card_requires_suit(self):
        with pytest.raises(ValueError):
            Card(Rank.SEVEN)

    def test_royal_card_requires_suit(self):
        with pytest.raises(ValueError):
            Card(Rank.KING)

    def test_animal_companion_requires_suit(self):
        with pytest.raises(ValueError):
            Card(Rank.ANIMAL_COMPANION)

    def test_jester_rejects_suit(self):
        with pytest.raises(ValueError):
            Card(Rank.JESTER, Suit.HEARTS)

    def test_jester_convenience_constructor(self):
        jester = Card.jester()
        assert jester.rank is Rank.JESTER
        assert jester.suit is None

    def test_animal_companion_convenience_constructor(self):
        ac = Card.animal_companion(Suit.CLUBS)
        assert ac.rank is Rank.ANIMAL_COMPANION
        assert ac.suit is Suit.CLUBS


class TestCardProperties:
    def test_value_matches_rank_attack_value(self):
        card = Card(Rank.QUEEN, Suit.SPADES)
        assert card.value == 15 == card.rank.attack_value

    def test_is_jester(self):
        assert Card.jester().is_jester
        assert not Card(Rank.TWO, Suit.HEARTS).is_jester

    def test_is_animal_companion(self):
        assert Card.animal_companion(Suit.HEARTS).is_animal_companion
        assert not Card(Rank.TWO, Suit.HEARTS).is_animal_companion

    def test_is_royal(self):
        for rank in (Rank.JACK, Rank.QUEEN, Rank.KING):
            assert Card(rank, Suit.HEARTS).is_royal
        assert not Card(Rank.TEN, Suit.HEARTS).is_royal
        assert not Card.jester().is_royal

    def test_is_number(self):
        assert Card(Rank.TWO, Suit.HEARTS).is_number
        assert not Card(Rank.JACK, Suit.HEARTS).is_number
        assert not Card.animal_companion(Suit.HEARTS).is_number


class TestCardEquality:
    def test_equal_by_value(self):
        assert Card(Rank.NINE, Suit.CLUBS) == Card(Rank.NINE, Suit.CLUBS)

    def test_hashable_for_use_in_sets(self):
        cards = {Card(Rank.NINE, Suit.CLUBS), Card(Rank.NINE, Suit.CLUBS)}
        assert len(cards) == 1

    def test_immutable(self):
        card = Card(Rank.NINE, Suit.CLUBS)
        with pytest.raises(Exception):
            card.rank = Rank.TEN
