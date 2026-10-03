from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.enemy import Enemy
from regicide.game_state import GameState
from regicide.game_view import GameView
from regicide.hand import Hand
from regicide.player import Player
from regicide.solo import SoloJesters


def make_state() -> tuple[Player, Player, GameState]:
    first = Player(
        "Player 1",
        Hand(5, [Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.CLUBS)]),
    )
    second = Player("Player 2", Hand(5, [Card(Rank.NINE, Suit.SPADES)]))
    state = GameState(
        [first, second],
        TavernDeck([Card(Rank.FOUR, Suit.DIAMONDS), Card(Rank.FIVE, Suit.CLUBS)]),
        DiscardPile([Card(Rank.SIX, Suit.HEARTS)]),
        CastleDeck([Card(Rank.QUEEN, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]),
        Enemy(Card(Rank.JACK, Suit.DIAMONDS)),
    )
    return first, second, state


class TestGameView:
    def test_exposes_viewing_players_hand(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).hand == ("2H", "3C")

    def test_opponents_expose_only_hand_size(self):
        first, _, state = make_state()
        view = GameView.for_player(first, state)
        assert view.players[1].hand_size == 1

    def test_serialized_opponent_contains_no_cards(self):
        first, _, state = make_state()
        opponent = GameView.for_player(first, state).to_dict()["players"][1]
        assert set(opponent) == {"name", "hand_size"}

    def test_exposes_current_enemy(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).enemy.card == "JD"

    def test_exposes_tavern_size(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).tavern_size == 2

    def test_exposes_castle_size(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).castle_size == 2

    def test_exposes_discard_cards(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).discard == ("6H",)

    def test_does_not_serialize_tavern_contents(self):
        first, _, state = make_state()
        serialized = GameView.for_player(first, state).to_dict()
        assert "tavern" not in serialized

    def test_does_not_serialize_castle_contents(self):
        first, _, state = make_state()
        serialized = GameView.for_player(first, state).to_dict()
        assert "castle" not in serialized

    def test_can_yield_for_current_player_when_allowed(self):
        first, _, state = make_state()
        assert GameView.for_player(first, state).can_yield is True

    def test_noncurrent_player_cannot_yield(self):
        _, second, state = make_state()
        assert GameView.for_player(second, state).can_yield is False

    def test_rejects_player_not_in_game(self):
        first, _, state = make_state()
        outsider = Player("Outsider", Hand(5))
        try:
            GameView.for_player(outsider, state)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    def test_exposes_solo_jesters_remaining(self):
        player = Player("Player 1", Hand(8, [Card(Rank.TWO, Suit.HEARTS)]))
        state = GameState(
            [player], TavernDeck(), DiscardPile(), CastleDeck(),
            Enemy(Card(Rank.JACK, Suit.CLUBS)), solo_jesters=SoloJesters(),
        )
        assert GameView.for_player(player, state).solo_jesters_remaining == 2


class TestCastleKnowledge:
    def test_current_enemy_is_in_encounter_history(self):
        first, _, state = make_state()
        assert state.encountered_enemies == [Card(Rank.JACK, Suit.DIAMONDS)]

    def test_remaining_suits_exclude_encountered_suits(self):
        first, _, state = make_state()
        state.encountered_enemies = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.JACK, Suit.DIAMONDS),
        ]
        knowledge = GameView.for_player(first, state).castle_knowledge
        assert knowledge.remaining_suits == ("Spades",)

    def test_fourth_enemy_is_known_after_three_suits_encountered(self):
        first, _, state = make_state()
        state.encountered_enemies = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.JACK, Suit.DIAMONDS),
        ]
        assert GameView.for_player(first, state).castle_knowledge.next_enemy == "JS"

    def test_next_enemy_is_unknown_with_two_suits_remaining(self):
        first, _, state = make_state()
        state.encountered_enemies = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
        ]
        assert GameView.for_player(first, state).castle_knowledge.next_enemy is None

    def test_other_rank_history_does_not_reduce_current_rank_possibilities(self):
        first, _, state = make_state()
        state.encountered_enemies = [
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.QUEEN, Suit.HEARTS),
        ]
        state.encounter = __import__("regicide.encounter", fromlist=["Encounter"]).Encounter(
            Enemy(Card(Rank.QUEEN, Suit.HEARTS))
        )
        knowledge = GameView.for_player(first, state).castle_knowledge
        assert set(knowledge.remaining_suits) == {"Diamonds", "Clubs", "Spades"}
