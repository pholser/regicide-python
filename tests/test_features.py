from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.enemy import Enemy
from regicide.features import FEATURE_NAMES, extract
from regicide.game_state import GameState
from regicide.hand import Hand
from regicide.player import Player
from regicide.solo import SoloJesters


def make_state(hand, tavern=(), discard=(), castle=(), enemy_card=Card(Rank.JACK, Suit.HEARTS)):
    player = Player("Player 1", Hand(max_size=8, cards=hand))
    state = GameState(
        players=[player],
        tavern=TavernDeck(list(tavern)),
        discard=DiscardPile(list(discard)),
        castle=CastleDeck(list(castle)),
        enemy=Enemy(enemy_card),
        solo_jesters=SoloJesters(),
    )
    return player, state


def test_feature_vector_matches_names():
    player, state = make_state([Card(Rank.TEN, Suit.SPADES), Card(Rank.TWO, Suit.CLUBS)])
    assert len(extract(player, state)) == len(FEATURE_NAMES)


def test_hand_and_enemy_features():
    player, state = make_state(
        [Card(Rank.TEN, Suit.SPADES), Card(Rank.TWO, Suit.CLUBS), Card(Rank.FIVE, Suit.DIAMONDS)],
        tavern=[Card(Rank.FOUR, Suit.HEARTS)] * 4,
        discard=[Card(Rank.SIX, Suit.CLUBS)],
        castle=[Card(Rank.QUEEN, Suit.SPADES)],
    )
    values = dict(zip(FEATURE_NAMES, extract(player, state)))
    assert values["hand_size"] == 3
    assert values["hand_value"] == 17
    assert values["hand_spades"] == 1
    assert values["hand_diamonds"] == 1
    assert values["hand_clubs"] == 1
    assert values["hand_hearts"] == 0
    assert values["hand_spades_value"] == 10
    assert values["hand_diamonds_value"] == 5
    assert values["hand_clubs_value"] == 2
    assert values["hand_hearts_value"] == 0
    assert values["enemy_remaining_health"] == 20
    assert values["enemy_attack"] == 10
    assert values["enemy_shield"] == 0
    assert values["enemy_is_hearts"] == 1
    assert values["enemy_is_spades"] == 0
    assert values["enemy_immunity_active"] == 1
    assert values["tavern_size"] == 4
    assert values["discard_size"] == 1
    assert values["castle_size"] == 1
    assert values["solo_jesters_remaining"] == 2


def test_hidden_tavern_order_does_not_change_features():
    cards = [Card(Rank.TWO, Suit.HEARTS), Card(Rank.NINE, Suit.CLUBS), Card(Rank.FOUR, Suit.SPADES)]
    player_a, state_a = make_state([Card(Rank.TEN, Suit.SPADES)], tavern=cards)
    player_b, state_b = make_state([Card(Rank.TEN, Suit.SPADES)], tavern=list(reversed(cards)))
    assert extract(player_a, state_a) == extract(player_b, state_b)
