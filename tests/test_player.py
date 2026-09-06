import pytest

from regicide.cards import Card, Rank, Suit
from regicide.hand import CardNotInHand, Hand
from regicide.play import CardPlay
from regicide.player import InsufficientDiscard, Player

TWO_HEARTS = Card(Rank.TWO, Suit.HEARTS)
THREE_CLUBS = Card(Rank.THREE, Suit.CLUBS)
JESTER = Card.jester()


def make_player(*cards: Card, max_size: int = 5) -> Player:
    return Player(name="Alice", hand=Hand(max_size=max_size, cards=cards))


class TestPlay:
    def test_removes_played_cards_from_hand(self):
        player = make_player(TWO_HEARTS, THREE_CLUBS)
        player.play(CardPlay.create(TWO_HEARTS))
        assert set(player.hand.cards) == {THREE_CLUBS}

    def test_playing_a_card_not_in_hand_raises(self):
        player = make_player(TWO_HEARTS)
        with pytest.raises(CardNotInHand):
            player.play(CardPlay.create(THREE_CLUBS))


class TestCanSurvive:
    def test_true_when_hand_totals_at_least_amount(self):
        player = make_player(TWO_HEARTS, THREE_CLUBS)  # total value 5
        assert player.can_survive(5)
        assert player.can_survive(4)
        assert not player.can_survive(6)

    def test_animal_companion_and_jester_use_their_own_values(self):
        player = make_player(Card.animal_companion(Suit.HEARTS), JESTER)
        assert player.can_survive(1)
        assert not player.can_survive(2)


class TestDiscard:
    def test_discard_removes_cards_and_returns_them(self):
        player = make_player(TWO_HEARTS, THREE_CLUBS)
        discarded = player.discard([TWO_HEARTS, THREE_CLUBS], amount=5)
        assert set(discarded) == {TWO_HEARTS, THREE_CLUBS}
        assert player.hand.is_empty

    def test_insufficient_discard_raises_and_removes_nothing(self):
        player = make_player(TWO_HEARTS, THREE_CLUBS)
        with pytest.raises(InsufficientDiscard):
            player.discard([TWO_HEARTS], amount=5)
        assert set(player.hand.cards) == {TWO_HEARTS, THREE_CLUBS}

    def test_discarding_a_card_not_in_hand_raises(self):
        player = make_player(TWO_HEARTS)
        with pytest.raises(CardNotInHand):
            player.discard([THREE_CLUBS], amount=1)
