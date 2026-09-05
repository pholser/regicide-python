import pytest

from regicide.cards import Card, Rank, Suit
from regicide.play import CardPlay, InvalidPlay, PlayKind


class TestSinglePlays:
    def test_plain_number_card(self):
        play = CardPlay.create(Card(Rank.SEVEN, Suit.HEARTS))
        assert play.kind is PlayKind.SINGLE
        assert play.total_attack_value == 7
        assert play.active_suits == {Suit.HEARTS}

    def test_royal_card(self):
        play = CardPlay.create(Card(Rank.KING, Suit.SPADES))
        assert play.kind is PlayKind.SINGLE
        assert play.total_attack_value == 20

    def test_animal_companion_alone(self):
        play = CardPlay.create(Card.animal_companion(Suit.DIAMONDS))
        assert play.kind is PlayKind.SINGLE
        assert play.total_attack_value == 1

    def test_jester_alone(self):
        play = CardPlay.create(Card.jester())
        assert play.kind is PlayKind.JESTER
        assert play.is_jester
        assert play.total_attack_value == 0
        assert play.active_suits == frozenset()


class TestAnimalCompanionPairing:
    def test_paired_with_number_card_matches_rulebook_example(self):
        # "the 8 of Diamonds with the Animal Companion of Clubs": attack
        # value 9, both Diamonds and Clubs powers apply.
        play = CardPlay.create(
            Card(Rank.EIGHT, Suit.DIAMONDS), Card.animal_companion(Suit.CLUBS)
        )
        assert play.kind is PlayKind.ANIMAL_COMPANION_PAIR
        assert play.total_attack_value == 9
        assert play.active_suits == {Suit.DIAMONDS, Suit.CLUBS}

    def test_paired_with_royal_card_is_allowed(self):
        play = CardPlay.create(
            Card.animal_companion(Suit.HEARTS), Card(Rank.KING, Suit.CLUBS)
        )
        assert play.total_attack_value == 21

    def test_paired_with_animal_companion_of_different_suit_applies_both_powers(self):
        play = CardPlay.create(
            Card.animal_companion(Suit.HEARTS), Card.animal_companion(Suit.SPADES)
        )
        assert play.total_attack_value == 2
        assert play.active_suits == {Suit.HEARTS, Suit.SPADES}

    def test_paired_with_same_suit_applies_power_once(self):
        play = CardPlay.create(
            Card(Rank.FIVE, Suit.CLUBS), Card.animal_companion(Suit.CLUBS)
        )
        assert play.active_suits == {Suit.CLUBS}

    def test_cannot_pair_with_jester(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(Card.animal_companion(Suit.HEARTS), Card.jester())

    def test_cannot_pair_with_two_other_cards(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(
                Card.animal_companion(Suit.HEARTS),
                Card(Rank.TWO, Suit.CLUBS),
                Card(Rank.THREE, Suit.SPADES),
            )


class TestCombos:
    def test_pair_of_fives_matches_rulebook_max(self):
        play = CardPlay.create(Card(Rank.FIVE, Suit.HEARTS), Card(Rank.FIVE, Suit.CLUBS))
        assert play.kind is PlayKind.COMBO
        assert play.total_attack_value == 10

    def test_triple_of_threes_matches_rulebook_example(self):
        # "3 of Diamonds, Spades and Clubs": attack value 9.
        play = CardPlay.create(
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.SPADES),
            Card(Rank.THREE, Suit.CLUBS),
        )
        assert play.total_attack_value == 9
        assert play.active_suits == {Suit.DIAMONDS, Suit.SPADES, Suit.CLUBS}

    def test_quadruple_twos(self):
        play = CardPlay.create(*(Card(Rank.TWO, suit) for suit in Suit))
        assert play.total_attack_value == 8

    def test_triple_fours_exceeds_ten(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(
                Card(Rank.FOUR, Suit.HEARTS),
                Card(Rank.FOUR, Suit.CLUBS),
                Card(Rank.FOUR, Suit.SPADES),
            )

    def test_pair_of_sixes_exceeds_ten(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(Card(Rank.SIX, Suit.HEARTS), Card(Rank.SIX, Suit.CLUBS))

    def test_mismatched_ranks_rejected(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.CLUBS))

    def test_pair_of_royals_rejected(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(Card(Rank.JACK, Suit.HEARTS), Card(Rank.JACK, Suit.CLUBS))

    def test_animal_companions_cannot_form_a_combo_on_their_own(self):
        # Two ACs is a valid pairing (covered above); this checks that a
        # same-suit AC "combo" of 3+ is still rejected as a pairing violation.
        with pytest.raises(InvalidPlay):
            CardPlay.create(
                Card.animal_companion(Suit.HEARTS),
                Card.animal_companion(Suit.CLUBS),
                Card.animal_companion(Suit.SPADES),
            )


class TestJesterRestrictions:
    def test_jester_must_be_alone(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(Card.jester(), Card(Rank.TWO, Suit.HEARTS))


class TestMalformedPlays:
    def test_empty_play_rejected(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create()

    def test_more_than_four_cards_rejected(self):
        with pytest.raises(InvalidPlay):
            CardPlay.create(
                Card(Rank.TWO, Suit.HEARTS),
                Card(Rank.TWO, Suit.CLUBS),
                Card(Rank.TWO, Suit.SPADES),
                Card(Rank.TWO, Suit.DIAMONDS),
                Card(Rank.THREE, Suit.HEARTS),
            )
