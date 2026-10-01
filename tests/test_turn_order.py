import pytest

from regicide.hand import Hand
from regicide.player import Player
from regicide.turn_order import IllegalAction, TurnOrder


def make_players(*names: str) -> list[Player]:
    return [Player(name=name, hand=Hand(max_size=5)) for name in names]


class TestConstruction:
    def test_rejects_duplicate_names(self):
        with pytest.raises(ValueError):
            TurnOrder(make_players("Alice", "Bob", "Alice"))

    def test_current_player_starts_at_seat_zero(self):
        players = make_players("Alice", "Bob")
        order = TurnOrder(players)
        assert order.current_player is players[0]


class TestAdvanceAndSetCurrent:
    def test_advance_moves_to_next_seat_and_wraps(self):
        players = make_players("Alice", "Bob", "Cara")
        order = TurnOrder(players)
        order.advance()
        assert order.current_player is players[1]
        order.advance()
        assert order.current_player is players[2]
        order.advance()
        assert order.current_player is players[0]

    def test_set_current_jumps_to_named_player(self):
        players = make_players("Alice", "Bob", "Cara")
        order = TurnOrder(players)
        order.set_current(players[2])
        assert order.current_player is players[2]

    def test_set_current_rejects_unknown_player(self):
        players = make_players("Alice", "Bob")
        order = TurnOrder(players)
        stranger = Player(name="Ghost", hand=Hand(max_size=5))
        with pytest.raises(IllegalAction):
            order.set_current(stranger)

    def test_clockwise_from_current_wraps_starting_at_current(self):
        players = make_players("Alice", "Bob", "Cara")
        order = TurnOrder(players)
        order.set_current(players[1])
        assert order.clockwise_from_current() == [players[1], players[2], players[0]]


class TestYieldStreak:
    def test_first_player_can_always_yield(self):
        order = TurnOrder(make_players("Alice", "Bob"))
        assert order.can_yield()

    def test_solo_play_can_never_yield(self):
        order = TurnOrder(make_players("Alice"))
        assert not order.can_yield()
        with pytest.raises(IllegalAction):
            order.yield_turn()
        order.mark_played()
        assert not order.can_yield()

    def test_two_player_blocks_after_one_yield(self):
        order = TurnOrder(make_players("Alice", "Bob"))
        order.yield_turn()
        order.advance()
        assert not order.can_yield()

    def test_three_player_blocks_only_after_both_others_yielded(self):
        order = TurnOrder(make_players("Alice", "Bob", "Cara"))
        order.yield_turn()
        order.advance()
        assert order.can_yield()  # only one of the two others has yielded so far
        order.yield_turn()
        order.advance()
        assert not order.can_yield()  # both other players yielded in a row

    def test_playing_a_card_resets_the_streak(self):
        order = TurnOrder(make_players("Alice", "Bob", "Cara"))
        order.yield_turn()
        order.advance()
        order.mark_played()
        order.advance()
        assert order.can_yield()

    def test_yield_turn_raises_when_illegal(self):
        order = TurnOrder(make_players("Alice", "Bob"))
        order.yield_turn()
        order.advance()
        with pytest.raises(IllegalAction):
            order.yield_turn()
