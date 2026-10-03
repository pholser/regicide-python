from regicide.actions import YIELD
from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.enemy import Enemy
from regicide.game_state import GameState
from regicide.hand import Hand
from regicide.legal_moves import legal_actions, legal_card_plays, legal_discards
from regicide.play import CardPlay
from regicide.player import Player


def card(rank: Rank, suit: Suit) -> Card:
    return Card(rank, suit)


def player_with(*cards: Card) -> Player:
    return Player("Player 1", Hand(max_size=8, cards=cards))


def state_with_players(*players: Player) -> GameState:
    return GameState(
        list(players), TavernDeck([]), DiscardPile(), CastleDeck([]),
        Enemy(Card(Rank.JACK, Suit.CLUBS)),
    )


class TestLegalCardPlays:
    def test_includes_each_single_card(self):
        two_hearts = card(Rank.TWO, Suit.HEARTS)
        five_spades = card(Rank.FIVE, Suit.SPADES)
        player = player_with(two_hearts, five_spades)
        plays = legal_card_plays(player)
        assert CardPlay.create(two_hearts) in plays
        assert CardPlay.create(five_spades) in plays

    def test_includes_same_rank_combo_totalling_at_most_ten(self):
        three_hearts = card(Rank.THREE, Suit.HEARTS)
        three_clubs = card(Rank.THREE, Suit.CLUBS)
        player = player_with(three_hearts, three_clubs)
        assert CardPlay.create(three_hearts, three_clubs) in legal_card_plays(player)

    def test_excludes_invalid_mixed_rank_pair(self):
        player = player_with(card(Rank.TWO, Suit.HEARTS), card(Rank.THREE, Suit.CLUBS))
        assert len(legal_card_plays(player)) == 2

    def test_includes_animal_companion_pair(self):
        companion = Card.animal_companion(Suit.HEARTS)
        ten_clubs = card(Rank.TEN, Suit.CLUBS)
        player = player_with(companion, ten_clubs)
        assert CardPlay.create(companion, ten_clubs) in legal_card_plays(player)

    def test_jester_is_only_offered_alone(self):
        jester = Card.jester()
        two_hearts = card(Rank.TWO, Suit.HEARTS)
        player = player_with(jester, two_hearts)
        assert legal_card_plays(player) == (CardPlay.create(jester), CardPlay.create(two_hearts))


class TestLegalActions:
    def test_includes_yield_when_turn_order_allows_it(self):
        first = player_with(card(Rank.TWO, Suit.HEARTS))
        second = Player("Player 2", Hand(max_size=8))
        state = state_with_players(first, second)
        assert legal_actions(first, state)[-1] is YIELD

    def test_excludes_yield_in_solo_play(self):
        player = player_with(card(Rank.TWO, Suit.HEARTS))
        state = state_with_players(player)
        assert YIELD not in legal_actions(player, state)

    def test_excludes_yield_after_every_other_player_yielded(self):
        first = player_with(card(Rank.TWO, Suit.HEARTS))
        second = Player("Player 2", Hand(max_size=8))
        state = state_with_players(first, second)
        state.turn_order.current_index = 1
        state.turn_order.yield_turn()
        state.turn_order.current_index = 0
        assert YIELD not in legal_actions(first, state)


class TestLegalDiscards:
    def test_includes_exact_discard(self):
        three = card(Rank.THREE, Suit.CLUBS)
        five = card(Rank.FIVE, Suit.SPADES)
        player = player_with(three, five)
        assert (three, five) in legal_discards(player, 8)

    def test_includes_overpaying_discard(self):
        five = card(Rank.FIVE, Suit.SPADES)
        seven = card(Rank.SEVEN, Suit.DIAMONDS)
        player = player_with(five, seven)
        assert (five, seven) in legal_discards(player, 8)

    def test_excludes_insufficient_discard(self):
        player = player_with(card(Rank.TWO, Suit.HEARTS), card(Rank.THREE, Suit.CLUBS))
        assert legal_discards(player, 6) == ()
