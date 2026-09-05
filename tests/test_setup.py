import pytest

from regicide.setup import jester_count, max_hand_size


@pytest.mark.parametrize("num_players,expected", [(1, 8), (2, 7), (3, 6), (4, 5)])
def test_max_hand_size(num_players, expected):
    assert max_hand_size(num_players) == expected


@pytest.mark.parametrize("num_players,expected", [(1, 0), (2, 0), (3, 1), (4, 2)])
def test_jester_count(num_players, expected):
    assert jester_count(num_players) == expected


@pytest.mark.parametrize("num_players", [0, 5])
def test_rejects_unsupported_player_counts(num_players):
    with pytest.raises(ValueError):
        max_hand_size(num_players)
    with pytest.raises(ValueError):
        jester_count(num_players)
