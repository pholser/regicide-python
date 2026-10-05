import random

from regicide.benchmark import (
    GreedyDecisions,
    DiamondsTimingDecisions,
    GreedyRescueDecisions,
    LookaheadDecisions,
    ShieldFirstDecisions,
    SuitAwareDecisions,
    play_game,
)
from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.enemy import Enemy
from regicide.game_state import GameState
from regicide.hand import Hand
from regicide.legal_moves import legal_card_plays
from regicide.player import Player
from regicide.solo import SoloJesters


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


def test_greedy_rescue_flips_only_when_hand_cannot_cover_attack():
    state = GameState.new_game(1, random.Random(1))
    rescue = GreedyRescueDecisions()
    weak = Player("P1", Hand(max_size=8, cards=[Card(Rank.TWO, Suit.CLUBS)]))
    strong = Player("P1", Hand(max_size=8, cards=[
        Card(Rank.TEN, Suit.CLUBS), Card(Rank.TEN, Suit.DIAMONDS),
    ]))
    assert rescue.choose_use_jester(weak, state)
    assert not rescue.choose_use_jester(strong, state)


def test_shield_first_prefers_a_spades_play_over_higher_damage():
    hand = Hand(max_size=8, cards=[Card(Rank.NINE, Suit.SPADES), Card(Rank.TEN, Suit.CLUBS)])
    player = Player("P1", hand)
    state = GameState(
        players=[player],
        tavern=TavernDeck(),
        discard=DiscardPile(),
        castle=CastleDeck(),
        enemy=Enemy(Card(Rank.JACK, Suit.HEARTS)),
        solo_jesters=SoloJesters(),
    )
    play = ShieldFirstDecisions().choose_action(player, state)
    assert play.cards == (Card(Rank.NINE, Suit.SPADES),)


def _state_with_hand(cards):
    player = Player("P1", Hand(max_size=8, cards=cards))
    state = GameState(
        players=[player],
        tavern=TavernDeck(),
        discard=DiscardPile(),
        castle=CastleDeck(),
        enemy=Enemy(Card(Rank.JACK, Suit.HEARTS)),
        solo_jesters=SoloJesters(),
    )
    return player, state


def test_diamonds_timing_holds_diamonds_back_when_hand_is_comfortable():
    player, state = _state_with_hand([
        Card(Rank.TEN, Suit.DIAMONDS), Card(Rank.SIX, Suit.CLUBS), Card(Rank.SIX, Suit.HEARTS),
    ])
    play = DiamondsTimingDecisions().choose_action(player, state)
    assert play.cards == (Card(Rank.SIX, Suit.CLUBS),)


def test_suit_aware_discard_keeps_spades_over_clubs_at_equal_cost():
    player, state = _state_with_hand([Card(Rank.FIVE, Suit.SPADES), Card(Rank.FIVE, Suit.CLUBS)])
    cover = SuitAwareDecisions().choose_discard(player, 5, state)
    assert cover == (Card(Rank.FIVE, Suit.CLUBS),)


def test_lookahead_returns_one_of_the_legal_plays():
    player, state = _state_with_hand([Card(Rank.TEN, Suit.DIAMONDS), Card(Rank.TWO, Suit.CLUBS)])
    play = LookaheadDecisions(random.Random(0), rollouts=2).choose_action(player, state)
    assert play in legal_card_plays(player)


def test_diamonds_timing_prefers_diamonds_when_hand_is_low():
    player, state = _state_with_hand([Card(Rank.TEN, Suit.DIAMONDS), Card(Rank.TWO, Suit.CLUBS)])
    play = DiamondsTimingDecisions().choose_action(player, state)
    assert play.cards == (Card(Rank.TEN, Suit.DIAMONDS),)
