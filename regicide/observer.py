from __future__ import annotations

from typing import Protocol

from regicide.cards import Card
from regicide.enemy import Enemy
from regicide.play import CardPlay
from regicide.player import Player


class TurnObserver(Protocol):
    """Notified of what happened as a turn resolves, so a UI can narrate it
    without the engine knowing anything about how (or whether) it's shown.
    Each method corresponds to one rule effect from Steps 1-4.
    """

    def on_yield(self, player: Player) -> None: ...

    def on_play(self, player: Player, play: CardPlay) -> None: ...

    def on_hearts(self, healed: int, blocked: bool) -> None: ...

    def on_diamonds(self, drawn: int, blocked: bool) -> None: ...

    def on_damage_dealt(self, enemy: Enemy, amount: int, doubled: bool) -> None: ...

    def on_shield_added(self, enemy: Enemy, amount: int) -> None: ...

    def on_jester_negated_immunity(self, enemy: Enemy) -> None: ...

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None: ...

    def on_enemy_revealed(self, enemy: Enemy) -> None: ...

    def on_player_suffered(self, player: Player, amount: int, discarded: tuple[Card, ...]) -> None: ...


class NullObserver:
    """A TurnObserver that does nothing, for callers that don't care."""

    def on_yield(self, player: Player) -> None:
        pass

    def on_play(self, player: Player, play: CardPlay) -> None:
        pass

    def on_hearts(self, healed: int, blocked: bool) -> None:
        pass

    def on_diamonds(self, drawn: int, blocked: bool) -> None:
        pass

    def on_damage_dealt(self, enemy: Enemy, amount: int, doubled: bool) -> None:
        pass

    def on_shield_added(self, enemy: Enemy, amount: int) -> None:
        pass

    def on_jester_negated_immunity(self, enemy: Enemy) -> None:
        pass

    def on_enemy_defeated(self, enemy: Enemy, exact: bool) -> None:
        pass

    def on_enemy_revealed(self, enemy: Enemy) -> None:
        pass

    def on_player_suffered(self, player: Player, amount: int, discarded: tuple[Card, ...]) -> None:
        pass


NULL_OBSERVER = NullObserver()
