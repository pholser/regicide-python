from __future__ import annotations

import random
from enum import Enum
from typing import TYPE_CHECKING

from regicide.actions import Yield
from regicide.cards import Card, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.encounter import Encounter
from regicide.enemy import Enemy
from regicide.hand import Hand
from regicide.observer import NULL_OBSERVER, TurnObserver
from regicide.play import CardPlay
from regicide.player import Player
from regicide.setup import max_hand_size
from regicide.turn_order import TurnOrder

if TYPE_CHECKING:
    from regicide.decisions import Decisions


class GameOutcome(Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class GameState:
    """The full state of a game in progress.

    Delegates seating/turn-order/yield-streak bookkeeping to ``turn_order``
    and the current enemy's fight to ``encounter``; this class coordinates
    those two plus the shared decks, since it's the only thing holding all
    of them together.
    """

    def __init__(
        self,
        players: list[Player],
        tavern: TavernDeck,
        discard: DiscardPile,
        castle: CastleDeck,
        enemy: Enemy,
        current_player_index: int = 0,
    ) -> None:
        self.turn_order = TurnOrder(players)
        self.turn_order.current_index = current_player_index
        self.tavern = tavern
        self.discard = discard
        self.castle = castle
        self.encounter = Encounter(enemy)
        self.outcome = GameOutcome.IN_PROGRESS

    @property
    def players(self) -> list[Player]:
        return self.turn_order.players

    @property
    def current_player(self) -> Player:
        return self.turn_order.current_player

    @property
    def enemy(self) -> Enemy:
        return self.encounter.enemy

    @property
    def cards_in_play(self) -> list[Card]:
        return self.encounter.cards_in_play

    @property
    def is_over(self) -> bool:
        return self.outcome is not GameOutcome.IN_PROGRESS

    @classmethod
    def new_game(cls, num_players: int, rng: random.Random) -> GameState:
        """Set up a new game per the SETUP section of the rules."""
        hand_size = max_hand_size(num_players)
        tavern = TavernDeck.build(num_players, rng)
        castle = CastleDeck.build(rng)

        players = [Player(name=f"Player {i + 1}", hand=Hand(hand_size)) for i in range(num_players)]
        for player in players:
            for _ in range(hand_size):
                card = tavern.draw()
                if card is None:
                    break
                player.hand.add(card)

        first_enemy_card = castle.draw_next()
        assert first_enemy_card is not None  # the Castle deck always starts with 12 cards
        enemy = Enemy(first_enemy_card)

        return cls(players, tavern, DiscardPile(), castle, enemy)

    def apply_red_suit_powers(
        self, play: CardPlay, rng: random.Random, observer: TurnObserver = NULL_OBSERVER
    ) -> None:
        """Hearts and Diamonds resolve immediately in Step 2 (Hearts first,
        when both are present). Clubs/Spades are handled by
        ``Enemy.resolve_play`` since their effect is entirely local to the
        enemy's own state (damage doubling, shield)."""
        amount = play.total_attack_value
        if Suit.HEARTS in play.active_suits:
            blocked = self.enemy.is_suit_blocked(Suit.HEARTS)
            healed = 0 if blocked else self.discard.heal_into(self.tavern, amount, rng)
            observer.on_hearts(healed, blocked)
        if Suit.DIAMONDS in play.active_suits:
            blocked = self.enemy.is_suit_blocked(Suit.DIAMONDS)
            drawn = 0 if blocked else self.draw_for_diamonds(amount)
            observer.on_diamonds(drawn, blocked)

    def draw_for_diamonds(self, amount: int) -> int:
        order = self.turn_order.clockwise_from_current()
        remaining = amount
        made_progress = True
        while remaining > 0 and made_progress:
            made_progress = False
            for player in order:
                if remaining <= 0:
                    break
                if self.tavern.is_empty:
                    return amount - remaining
                if player.hand.is_full:
                    continue
                player.hand.add(self.tavern.draw())
                remaining -= 1
                made_progress = True
        return amount - remaining

    def resolve_enemy_defeat(self) -> None:
        self.encounter.defeat(self.tavern, self.discard)
        next_card = self.castle.draw_next()
        if next_card is None:
            self.outcome = GameOutcome.WON
        else:
            self.encounter = Encounter(Enemy(next_card))

    def play_turn(
        self, decisions: Decisions, rng: random.Random, observer: TurnObserver = NULL_OBSERVER
    ) -> None:
        """Play one full turn (Steps 1-4).

        Loops rather than recurses when an enemy is defeated, since the
        same player then immediately starts a new turn against the next.
        """
        if self.is_over:
            raise ValueError("cannot play a turn: the game has already ended")

        while True:
            player = self.current_player

            if player.hand.is_empty and not self.turn_order.can_yield():
                self.outcome = GameOutcome.LOST
                return

            action = decisions.choose_action(player, self)

            if isinstance(action, Yield):
                self.turn_order.yield_turn()
                observer.on_yield(player)
                self.suffer_enemy_attack(decisions, player, observer)
                if self.outcome is GameOutcome.IN_PROGRESS:
                    self.turn_order.advance()
                return

            play = action
            player.play(play)
            self.turn_order.mark_played()
            observer.on_play(player, play)

            if play.is_jester:
                self.encounter.negate_immunity()
                observer.on_jester_negated_immunity(self.enemy)
                self.encounter.record_play(play)
                next_player = decisions.choose_next_player(player, self)
                self.turn_order.set_current(next_player)
                return

            self.apply_red_suit_powers(play, rng, observer)
            result = self.encounter.resolve_play(play)
            observer.on_damage_dealt(self.enemy, result.damage_dealt, result.doubled)
            if Suit.SPADES in play.active_suits:
                observer.on_shield_added(self.enemy, result.shield_added)

            if result.defeated:
                exact = self.enemy.is_exactly_defeated
                defeated_enemy = self.enemy
                self.resolve_enemy_defeat()
                observer.on_enemy_defeated(defeated_enemy, exact)
                if self.is_over:
                    return
                observer.on_enemy_revealed(self.enemy)
                continue  # same player, new enemy, back to Step 1

            self.suffer_enemy_attack(decisions, player, observer)
            if self.outcome is GameOutcome.IN_PROGRESS:
                self.turn_order.advance()
            return

    def suffer_enemy_attack(
        self, decisions: Decisions, player: Player, observer: TurnObserver = NULL_OBSERVER
    ) -> None:
        amount = self.enemy.effective_attack
        if amount <= 0:
            return
        if not player.can_survive(amount):
            self.outcome = GameOutcome.LOST
            return
        chosen = decisions.choose_discard(player, amount, self)
        discarded = player.discard(chosen, amount)
        self.discard.add_all(discarded)
        observer.on_player_suffered(player, amount, discarded)
