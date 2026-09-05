import random

from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck

TWO_HEARTS = Card(Rank.TWO, Suit.HEARTS)
THREE_CLUBS = Card(Rank.THREE, Suit.CLUBS)
FOUR_SPADES = Card(Rank.FOUR, Suit.SPADES)


class TestTavernDeckDrawing:
    def test_draw_returns_top_card_first(self):
        deck = TavernDeck([TWO_HEARTS, THREE_CLUBS])
        assert deck.draw() == TWO_HEARTS
        assert deck.draw() == THREE_CLUBS

    def test_draw_from_empty_deck_returns_none(self):
        deck = TavernDeck()
        assert deck.is_empty
        assert deck.draw() is None

    def test_place_under_goes_to_the_bottom(self):
        deck = TavernDeck([TWO_HEARTS])
        deck.place_under([THREE_CLUBS, FOUR_SPADES])
        assert deck.draw() == TWO_HEARTS
        assert deck.draw() == THREE_CLUBS
        assert deck.draw() == FOUR_SPADES

    def test_size_tracks_contents(self):
        deck = TavernDeck([TWO_HEARTS, THREE_CLUBS])
        assert deck.size == 2
        deck.draw()
        assert deck.size == 1


class TestTavernDeckBuild:
    def test_composition_for_four_players(self):
        deck = TavernDeck.build(num_players=4, rng=random.Random(0))
        # 9 numbers (2-10) x 4 suits + 4 animal companions + 2 jesters
        assert deck.size == 9 * 4 + 4 + 2

    def test_composition_for_one_player_has_no_jesters(self):
        deck = TavernDeck.build(num_players=1, rng=random.Random(0))
        cards = []
        while (card := deck.draw()) is not None:
            cards.append(card)
        assert sum(1 for c in cards if c.is_jester) == 0
        assert sum(1 for c in cards if c.is_animal_companion) == 4
        assert all(not c.is_royal for c in cards)

    def test_deterministic_given_same_seed(self):
        first = TavernDeck.build(num_players=3, rng=random.Random(42))
        second = TavernDeck.build(num_players=3, rng=random.Random(42))
        drawn_first = [first.draw() for _ in range(first.size)]
        drawn_second = [second.draw() for _ in range(second.size)]
        assert drawn_first == drawn_second


class TestDiscardPile:
    def test_add_and_size(self):
        pile = DiscardPile()
        pile.add(TWO_HEARTS)
        pile.add_all([THREE_CLUBS, FOUR_SPADES])
        assert pile.size == 3
        assert set(pile.cards) == {TWO_HEARTS, THREE_CLUBS, FOUR_SPADES}

    def test_take_all_empties_the_pile(self):
        pile = DiscardPile([TWO_HEARTS, THREE_CLUBS])
        taken = pile.take_all()
        assert set(taken) == {TWO_HEARTS, THREE_CLUBS}
        assert pile.is_empty
        assert pile.size == 0

    def test_take_all_on_empty_pile_returns_empty_list(self):
        assert DiscardPile().take_all() == []


class TestCastleDeck:
    def test_build_orders_jacks_then_queens_then_kings(self):
        deck = CastleDeck.build(rng=random.Random(1))
        revealed = []
        while (card := deck.draw_next()) is not None:
            revealed.append(card)
        assert [c.rank for c in revealed[0:4]] == [Rank.JACK] * 4
        assert [c.rank for c in revealed[4:8]] == [Rank.QUEEN] * 4
        assert [c.rank for c in revealed[8:12]] == [Rank.KING] * 4
        assert {c.suit for c in revealed[0:4]} == set(Suit)
        assert {c.suit for c in revealed[4:8]} == set(Suit)
        assert {c.suit for c in revealed[8:12]} == set(Suit)

    def test_draw_next_from_empty_deck_returns_none(self):
        deck = CastleDeck()
        assert deck.draw_next() is None

    def test_deterministic_given_same_seed(self):
        first = CastleDeck.build(rng=random.Random(7))
        second = CastleDeck.build(rng=random.Random(7))
        drawn_first = [first.draw_next() for _ in range(first.size)]
        drawn_second = [second.draw_next() for _ in range(second.size)]
        assert drawn_first == drawn_second
