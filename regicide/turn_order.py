from __future__ import annotations

from regicide.player import Player


class IllegalAction(Exception):
    """Raised when an action violates the rules given the current turn
    state (e.g. yielding when the yield-streak rule forbids it, or naming
    a player who isn't seated in this game)."""


class TurnOrder:
    """Seating order, whose turn it is, and the yield-streak rule.

    A player may not yield if every other player yielded on their last
    turn -- tracked per-seat rather than by rotation position, so it stays
    correct even when the Jester sends the turn to an arbitrary seat.
    """

    def __init__(self, players: list[Player]) -> None:
        names = [player.name for player in players]
        if len(set(names)) != len(names):
            raise ValueError(f"player names must be unique, got {names}")

        self.players = players
        self.current_index = 0
        self._last_turn_was_yield = [False] * len(players)

    @property
    def current_player(self) -> Player:
        return self.players[self.current_index]

    def can_yield(self) -> bool:
        others = [i for i in range(len(self.players)) if i != self.current_index]
        if not others:
            return True  # solo play: no one else to have yielded
        return not all(self._last_turn_was_yield[i] for i in others)

    def yield_turn(self) -> None:
        if not self.can_yield():
            raise IllegalAction("cannot yield: every other player yielded last turn")
        self._last_turn_was_yield[self.current_index] = True

    def mark_played(self) -> None:
        self._last_turn_was_yield[self.current_index] = False

    def advance(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.players)

    def set_current(self, player: Player) -> None:
        try:
            self.current_index = self.players.index(player)
        except ValueError:
            raise IllegalAction(f"{player.name} is not seated in this game") from None

    def clockwise_from_current(self) -> list[Player]:
        i = self.current_index
        return self.players[i:] + self.players[:i]
