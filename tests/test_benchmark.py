import random

from regicide.benchmark import GreedyDecisions, play_game
from regicide.cards import Card, Rank, Suit
from regicide.game_state import GameState
from regicide.hand import Hand
from regicide.legal_moves import legal_card_plays
from regicide.player import Player


def test_same_seed_gives_same_result():
    for policy in ("random", "greedy"):
        assert play_game(5, policy) == play_game(5, policy)


def test_results_are_internally_consistent():
    for policy in ("random", "greedy"):
        for seed in range(1, 6):
            result = play_game(seed, policy)
            assert 0 <= result.enemies_defeated <= 12
            assert result.turns > 0
            if result.won:
                assert result.enemies_defeated == 12


def test_greedy_plays_the_highest_attack_card():
    state = GameState.new_game(1, random.Random(1))
    player = state.current_player
    play = GreedyDecisions().choose_action(player, state)
    assert play.total_attack_value == max(p.total_attack_value for p in legal_card_plays(player))


def test_greedy_discards_the_cheapest_cover():
    player = Player("P1", Hand(max_size=8, cards=[
        Card(Rank.TEN, Suit.SPADES), Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.THREE, Suit.DIAMONDS), Card(Rank.FIVE, Suit.HEARTS),
    ]))
    assert GreedyDecisions().choose_discard(player, 10, None) == (Card(Rank.TEN, Suit.SPADES),)
