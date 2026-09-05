"""Player-count-dependent constants from the SETUP section of the rules."""

from __future__ import annotations

_MAX_HAND_SIZE: dict[int, int] = {1: 8, 2: 7, 3: 6, 4: 5}
_JESTER_COUNT: dict[int, int] = {1: 0, 2: 0, 3: 1, 4: 2}


def max_hand_size(num_players: int) -> int:
    try:
        return _MAX_HAND_SIZE[num_players]
    except KeyError:
        raise ValueError(f"unsupported player count: {num_players}") from None


def jester_count(num_players: int) -> int:
    try:
        return _JESTER_COUNT[num_players]
    except KeyError:
        raise ValueError(f"unsupported player count: {num_players}") from None
