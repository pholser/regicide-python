from __future__ import annotations

from regicide.play import CardPlay


class Yield:
    """Sentinel for a player's Step 1 choice to yield instead of playing a card."""


YIELD = Yield()

Action = CardPlay | Yield
