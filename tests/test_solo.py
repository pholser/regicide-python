import pytest

from regicide.solo import SoloJesters, SoloVictoryTier


class TestSoloJesters:
    def test_starts_with_two_available(self):
        jesters = SoloJesters()
        assert jesters.remaining == 2
        assert jesters.used == 0
        assert jesters.available

    def test_use_decrements_remaining_and_increments_used(self):
        jesters = SoloJesters()
        jesters.use()
        assert jesters.remaining == 1
        assert jesters.used == 1
        assert jesters.available

    def test_raises_once_both_are_used(self):
        jesters = SoloJesters()
        jesters.use()
        jesters.use()
        assert not jesters.available
        with pytest.raises(ValueError):
            jesters.use()

    @pytest.mark.parametrize(
        "used,expected",
        [(0, SoloVictoryTier.GOLD), (1, SoloVictoryTier.SILVER), (2, SoloVictoryTier.BRONZE)],
    )
    def test_victory_tier_by_jesters_used(self, used, expected):
        jesters = SoloJesters()
        for _ in range(used):
            jesters.use()
        assert jesters.victory_tier is expected
