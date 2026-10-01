"""Test-only helpers, not collected by pytest as tests."""

from __future__ import annotations

from regicide.actions import Action
from regicide.cards import Card
from regicide.enemy import Enemy
from regicide.play import CardPlay
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
        self._use_jester: list[bool] = []

    def script_action(self, action: Action) -> None:
        self._actions.append(action)

    def script_discard(self, cards: list[Card]) -> None:
        self._discards.append(tuple(cards))

    def script_next_player(self, player: Player) -> None:
        self._next_players.append(player)

    def script_use_jester(self, use: bool) -> None:
        self._use_jester.append(use)

    def choose_action(self, player: Player, state: object) -> Action:
        assert self._actions, f"no scripted action left for {player.name}"
        return self._actions.pop(0)

    def choose_discard(self, player: Player, amount: int, state: object) -> tuple[Card, ...]:
        assert self._discards, f"no scripted discard left for {player.name}"
        return self._discards.pop(0)

    def choose_next_player(self, chooser: Player, state: object) -> Player:
        assert self._next_players, "no scripted next-player left"
        return self._next_players.pop(0)

    def choose_use_jester(self, player: Player, state: object) -> bool:
        # Defaults to "no" rather than asserting, since most tests never
        # exercise this solo-only, rarely-taken branch and shouldn't have to
        # script a response for every turn just to opt out of it.
        if self._use_jester:
            return self._use_jester.pop(0)
        return False


class RecordingObserver:
    """A TurnObserver that just records every call, as (method_name, args)
    tuples, so a test can assert on exactly what was reported."""

    def __init__(self) -> None:
        self.events: list[tuple[str, tuple]] = []

    def on_yield(self, player: Player) -> None:
        self.events.append(("on_yield", (player,)))

    def on_play(self, player: Player, play: CardPlay) -> None:
        self.events.append(("on_play", (player, play)))

    def on_hearts(self, healed: int, blocked: bool) -> None:
        self.events.append(("on_hearts", (healed, blocked)))

    def on_diamonds(self, drawn: int, blocked: bool) -> None:
        self.events.append(("on_diamonds", (drawn, blocked)))

    def on_damage_dealt(self, enemy: Enemy, amount: int, doubled: bool) -> None:
        self.events.append(("on_damage_dealt", (enemy, amount, doubled)))

    def on_shield_added(self, enemy: Enemy, amount: int) -> None:
        self.events.append(("on_shield_added", (enemy, amount)))

    def on_jester_negated_immunity(self, enemy: Enemy) -> None:
        self.events.append(("on_jester_negated_immunity", (enemy,)))

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None:
        self.events.append(("on_enemy_defeated", (enemy, exact)))

    def on_enemy_revealed(self, enemy: Enemy) -> None:
        self.events.append(("on_enemy_revealed", (enemy,)))

    def on_player_suffered(self, player: Player, amount: int, discarded: tuple[Card, ...]) -> None:
        self.events.append(("on_player_suffered", (player, amount, discarded)))

    def on_solo_jester_used(
        self, player: Player, discarded: tuple[Card, ...], drawn: int, remaining: int
    ) -> None:
        self.events.append(("on_solo_jester_used", (player, discarded, drawn, remaining)))
