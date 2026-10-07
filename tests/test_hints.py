import random

from regicide.benchmark import POLICIES
from regicide.cards import Card, Rank, Suit
from regicide.game_state import GameState
from regicide.hints import recommend
from regicide.legal_moves import legal_card_plays
from regicide.value_model import LinearValueModel


def test_recommend_returns_a_legal_play_without_changing_the_game():
    state = GameState.new_game(1, random.Random(4))
    hand_before = state.current_player.hand.cards
    tavern_before = state.tavern.size
    policy = POLICIES["greedy"](random.Random(4))
    hint = recommend("greedy", policy, state, random.Random(4), LinearValueModel.load())
    assert hint.play in legal_card_plays(state.current_player)
    assert state.current_player.hand.cards == hand_before
    assert state.tavern.size == tavern_before


def test_recommend_reports_a_winning_turn_as_game_over():
    from regicide.decks import CastleDeck, DiscardPile, TavernDeck
    from regicide.enemy import Enemy
    from regicide.hand import Hand
    from regicide.player import Player
    from regicide.solo import SoloJesters

    player = Player("Player 1", Hand(max_size=8, cards=[Card(Rank.TEN, Suit.CLUBS)]))
    state = GameState(
        players=[player],
        tavern=TavernDeck(),
        discard=DiscardPile(),
        castle=CastleDeck(),
        enemy=Enemy(Card(Rank.JACK, Suit.DIAMONDS)),
        solo_jesters=SoloJesters(),
    )
    hint = recommend("greedy", POLICIES["greedy"](random.Random(0)), state, random.Random(0), LinearValueModel(0.0, (0.0,) * 21))
    assert hint.game_over
    assert hint.model_estimate == 12
