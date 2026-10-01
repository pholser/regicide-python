from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from regicide.actions import Action
from regicide.cards import Card
from regicide.player import Player

if TYPE_CHECKING:
    from regicide.game_state import GameState


class Decisions(Protocol):
    """The seam between the rules engine and whoever is actually choosing:
    a human via some UI, a bot, or a scripted test double. The engine only
    ever calls these three methods and never touches input/output directly.
    """

    def choose_action(self, player: Player, state: GameState) -> Action:
        """Step 1: play a CardPlay from ``player``'s hand, or return YIELD."""
        ...

    def choose_discard(self, player: Player, amount: int, state: GameState) -> tuple[Card, ...]:
        """Step 4: choose cards from ``player``'s hand summing to at least ``amount``."""
        ...

    def choose_next_player(self, chooser: Player, state: GameState) -> Player:
        """After a Jester: pick who goes next (any player, including ``chooser``)."""
        ...

    def choose_use_jester(self, player: Player, state: GameState) -> bool:
        """Solo play only, offered at the start of Step 1 and Step 4 while a
        Jester remains: flip one to discard the hand and refill it?"""
        ...
