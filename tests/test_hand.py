import pytest

from regicide.cards import Card, Rank, Suit
from regicide.hand import CardNotInHand, Hand, HandFullError

TWO_HEARTS = Card(Rank.TWO, Suit.HEARTS)
THREE_CLUBS = Card(Rank.THREE, Suit.CLUBS)


class TestConstruction:
    def test_starts_with_given_cards(self):
        hand = Hand(max_size=5, cards=[TWO_HEARTS, THREE_CLUBS])
        assert hand.size == 2
        assert set(hand.cards) == {TWO_HEARTS, THREE_CLUBS}

    def test_rejects_more_cards_than_max_size(self):
        with pytest.raises(ValueError):
            Hand(max_size=1, cards=[TWO_HEARTS, THREE_CLUBS])


class TestAdd:
    def test_add_increases_size(self):
        hand = Hand(max_size=2)
        hand.add(TWO_HEARTS)
        assert hand.size == 1
        assert TWO_HEARTS in hand

    def test_add_beyond_max_size_raises(self):
        hand = Hand(max_size=1, cards=[TWO_HEARTS])
        assert hand.is_full
        with pytest.raises(HandFullError):
            hand.add(THREE_CLUBS)
        assert hand.size == 1  # rejected add did not mutate the hand


class TestRemove:
    def test_remove_existing_card(self):
        hand = Hand(max_size=5, cards=[TWO_HEARTS, THREE_CLUBS])
        hand.remove(TWO_HEARTS)
        assert TWO_HEARTS not in hand
        assert hand.size == 1

    def test_remove_missing_card_raises(self):
        hand = Hand(max_size=5, cards=[TWO_HEARTS])
        with pytest.raises(CardNotInHand):
            hand.remove(THREE_CLUBS)


class TestState:
    def test_is_empty(self):
        assert Hand(max_size=3).is_empty
        assert not Hand(max_size=3, cards=[TWO_HEARTS]).is_empty

    def test_is_full(self):
        hand = Hand(max_size=1)
        assert not hand.is_full
        hand.add(TWO_HEARTS)
        assert hand.is_full

    def test_len_and_iter(self):
        hand = Hand(max_size=5, cards=[TWO_HEARTS, THREE_CLUBS])
        assert len(hand) == 2
        assert set(iter(hand)) == {TWO_HEARTS, THREE_CLUBS}

    def test_cards_property_is_a_snapshot(self):
        hand = Hand(max_size=5, cards=[TWO_HEARTS])
        snapshot = hand.cards
        hand.add(THREE_CLUBS)
        assert snapshot == (TWO_HEARTS,)  # unaffected by later mutation
        assert isinstance(hand.cards, tuple)
