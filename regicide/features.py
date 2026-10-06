"""Numeric features of a solo game state, limited to what the player can see.

The Tavern's order and the unseen cards are excluded: only the hand, the enemy,
pile sizes, and remaining Jesters go into the vector.
"""

from __future__ import annotations

from regicide.cards import Card, Suit
from regicide.game_state import GameState
from regicide.player import Player

FEATURE_NAMES: tuple[str, ...] = (
    "hand_size",
    "hand_value",
    "hand_spades",
    "hand_diamonds",
    "hand_clubs",
    "hand_hearts",
    "hand_spades_value",
    "hand_diamonds_value",
    "hand_clubs_value",
    "hand_hearts_value",
    "enemy_remaining_health",
    "enemy_attack",
    "enemy_effective_attack",
    "enemy_shield",
    "enemy_is_spades",
    "enemy_is_diamonds",
    "enemy_is_clubs",
    "tavern_size",
    "discard_size",
    "castle_size",
    "solo_jesters_remaining",
)


def extract(player: Player, state: GameState) -> tuple[float, ...]:
    hand = player.hand.cards
    enemy = state.enemy
    jesters = state.solo_jesters.remaining if state.solo_jesters is not None else 0
    return (
        float(len(hand)),
        float(sum(card.value for card in hand)),
        float(sum(card.suit is Suit.SPADES for card in hand)),
        float(sum(card.suit is Suit.DIAMONDS for card in hand)),
        float(sum(card.suit is Suit.CLUBS for card in hand)),
        float(sum(card.suit is Suit.HEARTS for card in hand)),
        float(_suit_value(hand, Suit.SPADES)),
        float(_suit_value(hand, Suit.DIAMONDS)),
        float(_suit_value(hand, Suit.CLUBS)),
        float(_suit_value(hand, Suit.HEARTS)),
        float(enemy.remaining_health),
        float(enemy.attack),
        float(enemy.effective_attack),
        float(enemy.shield),
        float(enemy.card.suit is Suit.SPADES),
        float(enemy.card.suit is Suit.DIAMONDS),
        float(enemy.card.suit is Suit.CLUBS),
        float(state.tavern.size),
        float(state.discard.size),
        float(state.castle.size),
        float(jesters),
    )


def _suit_value(hand: tuple[Card, ...], suit: Suit) -> int:
    return sum(card.value for card in hand if card.suit is suit)
