"""Test-only helpers, not collected by pytest as tests."""

from __future__ import annotations

from regicide.actions import Action
from regicide.cards import Card
from regicide.player import Player


class ScriptedDecisions:
    """A Decisions implementation driven by pre-programmed responses.

    Each kind of call is answered from its own queue, in the order
    ``script_*`` was called. Calling past the end of a queue raises
    AssertionError -- that's a bug in the test's script, not a game rule
    violation, so it's kept distinct from the engine's own exceptions.
    """

    def __init__(self) -> None:
        self._actions: list[Action] = []
        self._discards: list[tuple[Card, ...]] = []
        self._next_players: list[Player] = []

    def script_action(self, action: Action) -> None:
        self._actions.append(action)

    def script_discard(self, cards: list[Card]) -> None:
        self._discards.append(tuple(cards))

    def script_next_player(self, player: Player) -> None:
        self._next_players.append(player)

    def choose_action(self, player: Player, state: object) -> Action:
        assert self._actions, f"no scripted action left for {player.name}"
        return self._actions.pop(0)

    def choose_discard(self, player: Player, amount: int, state: object) -> tuple[Card, ...]:
        assert self._discards, f"no scripted discard left for {player.name}"
        return self._discards.pop(0)

    def choose_next_player(self, chooser: Player, state: object) -> Player:
        assert self._next_players, "no scripted next-player left"
        return self._next_players.pop(0)
