"""The solo-play variant from the SOLO PLAY section of the rules.

With a single player, the two Jesters are not shuffled into the Tavern deck;
instead they're set aside and each can be flipped once -- at the start of
Step 1 (before playing a card) or Step 4 (before suffering damage) -- to
discard the hand and refill it to max size. Flipping a Jester this way does
not negate enemy immunity, unlike playing one from hand in multiplayer.
"""

from __future__ import annotations

from enum import Enum

_JESTER_SUPPLY = 2


class SoloVictoryTier(Enum):
    GOLD = "Gold Victory"
    SILVER = "Silver Victory"
    BRONZE = "Bronze Victory"


_TIERS_BY_USED: dict[int, SoloVictoryTier] = {
    0: SoloVictoryTier.GOLD,
    1: SoloVictoryTier.SILVER,
    2: SoloVictoryTier.BRONZE,
}


class SoloJesters:
    """The two Jesters set aside for solo play. ``use`` is the only way to
    spend one, so ``remaining``/``used`` can't drift out of sync."""

    def __init__(self, count: int = _JESTER_SUPPLY) -> None:
        self._remaining = count
        self._used = 0

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def used(self) -> int:
        return self._used

    @property
    def available(self) -> bool:
        return self._remaining > 0

    def use(self) -> None:
        if not self.available:
            raise ValueError("no Jesters remaining to flip")
        self._remaining -= 1
        self._used += 1

    @property
    def victory_tier(self) -> SoloVictoryTier:
        return _TIERS_BY_USED[self._used]
