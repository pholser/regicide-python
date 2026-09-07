from regicide.cards import Card, Rank, Suit
from regicide.decks import DiscardPile, TavernDeck
from regicide.encounter import Encounter
from regicide.enemy import Enemy
from regicide.play import CardPlay


def make_encounter(rank=Rank.JACK, suit=Suit.HEARTS) -> Encounter:
    return Encounter(Enemy(Card(rank, suit)))


class TestRecordPlay:
    def test_record_play_accumulates_cards(self):
        encounter = make_encounter()
        encounter.record_play(CardPlay.create(Card(Rank.TWO, Suit.CLUBS)))
        encounter.record_play(CardPlay.create(Card(Rank.THREE, Suit.SPADES)))
        assert encounter.cards_in_play == [
            Card(Rank.TWO, Suit.CLUBS),
            Card(Rank.THREE, Suit.SPADES),
        ]


class TestResolvePlay:
    def test_resolve_play_records_and_damages_enemy(self):
        encounter = make_encounter(rank=Rank.JACK, suit=Suit.HEARTS)
        play = CardPlay.create(Card(Rank.NINE, Suit.SPADES))
        result = encounter.resolve_play(play)
        assert not result.defeated
        assert result.damage_dealt == 9
        assert result.shield_added == 9
        assert not result.doubled
        assert encounter.enemy.remaining_health == 11
        assert encounter.cards_in_play == [Card(Rank.NINE, Suit.SPADES)]

    def test_resolve_play_reports_defeat(self):
        encounter = make_encounter(rank=Rank.JACK, suit=Suit.HEARTS)
        result = encounter.resolve_play(CardPlay.create(Card(Rank.TEN, Suit.SPADES)))
        assert not result.defeated
        result = encounter.resolve_play(CardPlay.create(Card(Rank.TEN, Suit.CLUBS)))
        assert result.defeated
        assert result.doubled
        assert result.damage_dealt == 20


class TestNegateImmunity:
    def test_negate_immunity_delegates_to_enemy(self):
        encounter = make_encounter(suit=Suit.SPADES)
        assert encounter.enemy.is_suit_blocked(Suit.SPADES)
        encounter.negate_immunity()
        assert not encounter.enemy.is_suit_blocked(Suit.SPADES)


class TestDefeat:
    def test_overkill_discards_enemy_and_cards_in_play(self):
        encounter = make_encounter(rank=Rank.JACK, suit=Suit.HEARTS)
        encounter.resolve_play(CardPlay.create(Card(Rank.NINE, Suit.SPADES)))
        encounter.enemy.take_damage(100)  # force overkill
        tavern = TavernDeck()
        discard = DiscardPile()

        encounter.defeat(tavern, discard)

        assert tavern.is_empty
        assert set(discard.cards) == {
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
        }
        assert encounter.cards_in_play == []

    def test_exact_kill_places_enemy_facedown_on_top_of_tavern(self):
        encounter = make_encounter(rank=Rank.JACK, suit=Suit.HEARTS)
        encounter.resolve_play(CardPlay.create(Card(Rank.NINE, Suit.SPADES)))
        encounter.enemy.take_damage(11)  # lands exactly on 20 health
        assert encounter.enemy.is_exactly_defeated
        tavern = TavernDeck([Card(Rank.TWO, Suit.CLUBS)])
        discard = DiscardPile()

        encounter.defeat(tavern, discard)

        assert tavern.draw() == Card(Rank.JACK, Suit.HEARTS)
        assert tavern.draw() == Card(Rank.TWO, Suit.CLUBS)
        assert set(discard.cards) == {Card(Rank.NINE, Suit.SPADES)}
