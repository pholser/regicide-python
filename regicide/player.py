from __future__ import annotations

from dataclasses import dataclass

from regicide.hand import Hand


@dataclass
class Player:
    """A seat at the table. Turn order/seating is managed by whatever holds
    the list of Players, not by Player itself."""

    name: str
    hand: Hand
