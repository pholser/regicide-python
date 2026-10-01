import random

import pytest

from regicide.actions import YIELD
from regicide.cards import Card, Rank, Suit
from regicide.decks import CastleDeck, DiscardPile, TavernDeck
from regicide.enemy import Enemy
from regicide.game_state import GameOutcome, GameState
from regicide.hand import Hand
from regicide.play import CardPlay
from regicide.player import Player
from regicide.solo import SoloJesters, SoloVictoryTier
from regicide.turn_order import IllegalAction

from support import RecordingObserver, ScriptedDecisions


def make_game(
    hands: list[list[Card]],
    enemy_card: Card = Card(Rank.JACK, Suit.HEARTS),
    tavern: list[Card] | None = None,
    discard: list[Card] | None = None,
    castle: list[Card] | None = None,
    neutralize_attack: bool = False,
    solo_jesters: SoloJesters | None = None,
) -> GameState:
    players = [
        Player(name=f"P{i + 1}", hand=Hand(max_size=max(8, len(cards)), cards=cards))
        for i, cards in enumerate(hands)
    ]
    enemy = Enemy(enemy_card)
    if neutralize_attack:
        enemy.add_shield(enemy.attack)
    return GameState(
        players=players,
        tavern=TavernDeck(tavern or []),
        discard=DiscardPile(discard or []),
        castle=CastleDeck(castle or []),
        enemy=enemy,
        solo_jesters=solo_jesters,
    )


class TestYield:
    def test_yield_skips_to_step_four_and_advances(self):
        state = make_game(
            hands=[[Card(Rank.TEN, Suit.SPADES)], [Card(Rank.TWO, Suit.HEARTS)]],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(YIELD)
        decisions.script_discard([Card(Rank.TEN, Suit.SPADES)])

        state.play_turn(decisions, random.Random(0))

        assert state.players[0].hand.is_empty
        assert Card(Rank.TEN, Suit.SPADES) in state.discard.cards
        assert state.current_player is state.players[1]
        assert state.outcome is GameOutcome.IN_PROGRESS

    def test_yield_blocked_when_streak_rule_forbids(self):
        state = make_game(
            hands=[[Card(Rank.TEN, Suit.SPADES)], [Card(Rank.TEN, Suit.CLUBS)]],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(YIELD)
        state.play_turn(decisions, random.Random(0))
        assert state.current_player is state.players[1]

        decisions.script_action(YIELD)
        with pytest.raises(IllegalAction):
            state.play_turn(decisions, random.Random(0))

    def test_forced_loss_when_hand_empty_and_yield_blocked(self):
        state = make_game(hands=[[], []], neutralize_attack=True)
        decisions = ScriptedDecisions()
        decisions.script_action(YIELD)
        state.play_turn(decisions, random.Random(0))
        assert state.outcome is GameOutcome.IN_PROGRESS

        state.play_turn(decisions, random.Random(0))
        assert state.outcome is GameOutcome.LOST


class TestHeartsPower:
    def test_heals_cards_from_discard_under_tavern(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.SPADES),
            hands=[[Card(Rank.THREE, Suit.HEARTS)], [Card(Rank.TWO, Suit.CLUBS)]],
            discard=[
                Card(Rank.FOUR, Suit.SPADES),
                Card(Rank.FIVE, Suit.DIAMONDS),
                Card(Rank.SIX, Suit.CLUBS),
            ],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.THREE, Suit.HEARTS)))

        state.play_turn(decisions, random.Random(0))

        assert state.tavern.size == 3
        assert state.discard.is_empty
        assert state.enemy.remaining_health == 20 - 3

    def test_blocked_by_matching_enemy_immunity(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),
            hands=[[Card(Rank.THREE, Suit.HEARTS)], [Card(Rank.TWO, Suit.CLUBS)]],
            discard=[Card(Rank.FOUR, Suit.SPADES)],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.THREE, Suit.HEARTS)))

        state.play_turn(decisions, random.Random(0))

        assert state.tavern.is_empty
        assert Card(Rank.FOUR, Suit.SPADES) in state.discard.cards


class TestDiamondsPower:
    def test_draws_clockwise_skipping_full_hands(self):
        p1 = Player("P1", Hand(max_size=8, cards=[Card(Rank.FOUR, Suit.DIAMONDS)]))
        p2 = Player("P2", Hand(max_size=1, cards=[Card(Rank.TWO, Suit.CLUBS)]))  # already full
        p3 = Player("P3", Hand(max_size=8, cards=[]))
        tavern_cards = [
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.SIX, Suit.HEARTS),
            Card(Rank.SEVEN, Suit.HEARTS),
            Card(Rank.EIGHT, Suit.HEARTS),
        ]
        enemy = Enemy(Card(Rank.JACK, Suit.SPADES))
        enemy.add_shield(enemy.attack)  # neutralize Step 4 for this test
        state = GameState(
            players=[p1, p2, p3],
            tavern=TavernDeck(tavern_cards),
            discard=DiscardPile(),
            castle=CastleDeck(),
            enemy=enemy,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.FOUR, Suit.DIAMONDS)))

        state.play_turn(decisions, random.Random(0))

        assert set(p1.hand.cards) == {Card(Rank.FIVE, Suit.HEARTS), Card(Rank.SEVEN, Suit.HEARTS)}
        assert set(p2.hand.cards) == {Card(Rank.TWO, Suit.CLUBS)}  # never drew, stayed full
        assert set(p3.hand.cards) == {Card(Rank.SIX, Suit.HEARTS), Card(Rank.EIGHT, Suit.HEARTS)}
        assert state.tavern.is_empty


class TestRedSuitOrdering:
    def test_hearts_resolves_before_diamonds_in_a_combined_play(self):
        # Hearts buries 5 cards (attack value 4+1) under the then-empty
        # Tavern deck; Diamonds then draws 5. If Diamonds resolved first,
        # the empty Tavern deck would have nothing to supply.
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.SPADES),
            hands=[[Card(Rank.FOUR, Suit.HEARTS), Card.animal_companion(Suit.DIAMONDS)]],
            discard=[
                Card(Rank.TWO, Suit.SPADES),
                Card(Rank.THREE, Suit.SPADES),
                Card(Rank.SIX, Suit.CLUBS),
                Card(Rank.SEVEN, Suit.CLUBS),
                Card(Rank.EIGHT, Suit.CLUBS),
                Card(Rank.NINE, Suit.CLUBS),
            ],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(
            CardPlay.create(Card(Rank.FOUR, Suit.HEARTS), Card.animal_companion(Suit.DIAMONDS))
        )

        state.play_turn(decisions, random.Random(0))

        assert state.players[0].hand.size == 5
        assert state.tavern.is_empty
        assert state.discard.size == 1


class TestComboImmunity:
    def test_immunity_to_one_suit_does_not_block_the_others_in_the_same_combo(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.DIAMONDS),  # immune to Diamonds only
            hands=[[
                Card(Rank.THREE, Suit.DIAMONDS),
                Card(Rank.THREE, Suit.SPADES),
                Card(Rank.THREE, Suit.CLUBS),
            ]],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(
            CardPlay.create(
                Card(Rank.THREE, Suit.DIAMONDS),
                Card(Rank.THREE, Suit.SPADES),
                Card(Rank.THREE, Suit.CLUBS),
            )
        )
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        assert state.enemy.remaining_health == 20 - 18  # Clubs doubled 9 -> 18, unblocked
        assert state.enemy.shield == 10 + 9  # pre-set neutralizing shield + Spades, unblocked
        _, (drawn, blocked) = next((n, a) for n, a in observer.events if n == "on_diamonds")
        assert drawn == 0
        assert blocked  # only Diamonds was blocked by the enemy's matching immunity


class TestSoloYielding:
    def test_cannot_yield_in_solo_play(self):
        state = make_game(hands=[[Card(Rank.TWO, Suit.HEARTS)]])
        decisions = ScriptedDecisions()
        decisions.script_action(YIELD)
        with pytest.raises(IllegalAction):
            state.play_turn(decisions, random.Random(0))

    def test_forced_loss_when_hand_empties_in_solo_play(self):
        state = make_game(hands=[[]])
        state.play_turn(ScriptedDecisions(), random.Random(0))
        assert state.outcome is GameOutcome.LOST


class TestSoloJesters:
    def test_flip_discards_hand_and_refills_without_negating_immunity(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.CLUBS),  # immune to Clubs
            hands=[[Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.SPADES)]],
            tavern=[Card(Rank.FOUR, Suit.DIAMONDS), Card(Rank.FIVE, Suit.DIAMONDS)],
            solo_jesters=SoloJesters(),
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_use_jester(True)
        decisions.script_action(CardPlay.create(Card(Rank.FOUR, Suit.DIAMONDS)))
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        assert state.solo_jesters.remaining == 1
        assert state.solo_jesters.used == 1
        assert state.enemy.is_suit_blocked(Suit.CLUBS)  # flipping doesn't negate immunity
        assert Card(Rank.TWO, Suit.HEARTS) in state.discard.cards
        assert Card(Rank.THREE, Suit.SPADES) in state.discard.cards
        _, (player, discarded, drawn, remaining) = next(
            (n, a) for n, a in observer.events if n == "on_solo_jester_used"
        )
        assert drawn == 2
        assert remaining == 1

    def test_flip_at_step_four_can_rescue_a_player_from_otherwise_fatal_damage(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),  # attack 10, immune to Hearts only
            hands=[[Card(Rank.TWO, Suit.CLUBS)]],  # hand value 2, nowhere near enough
            tavern=[Card(Rank.TEN, Suit.SPADES)] * 8,
            solo_jesters=SoloJesters(),
        )
        decisions = ScriptedDecisions()
        decisions.script_use_jester(False)  # Step 1 offer: declined
        decisions.script_action(CardPlay.create(Card(Rank.TWO, Suit.CLUBS)))
        decisions.script_use_jester(True)  # Step 4 offer: flip before suffering damage
        decisions.script_discard([Card(Rank.TEN, Suit.SPADES)])

        state.play_turn(decisions, random.Random(0))

        assert state.outcome is GameOutcome.IN_PROGRESS
        assert state.solo_jesters.used == 1


class TestSoloVictoryTier:
    def test_gold_when_no_jesters_used(self):
        state = make_game(
            enemy_card=Card(Rank.KING, Suit.DIAMONDS),
            hands=[[Card(Rank.KING, Suit.CLUBS)]],
            castle=[],
            solo_jesters=SoloJesters(),
        )
        decisions = ScriptedDecisions()
        decisions.script_use_jester(False)
        decisions.script_action(CardPlay.create(Card(Rank.KING, Suit.CLUBS)))

        state.play_turn(decisions, random.Random(0))

        assert state.outcome is GameOutcome.WON
        assert state.solo_victory_tier is SoloVictoryTier.GOLD

    def test_bronze_when_both_jesters_used(self):
        jesters = SoloJesters()
        jesters.use()
        jesters.use()
        state = make_game(
            enemy_card=Card(Rank.KING, Suit.DIAMONDS),
            hands=[[Card(Rank.KING, Suit.CLUBS)]],
            castle=[],
            solo_jesters=jesters,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.KING, Suit.CLUBS)))

        state.play_turn(decisions, random.Random(0))

        assert state.outcome is GameOutcome.WON
        assert state.solo_victory_tier is SoloVictoryTier.BRONZE

    def test_none_when_not_solo(self):
        state = make_game(hands=[[Card(Rank.TWO, Suit.HEARTS)], [Card(Rank.TWO, Suit.CLUBS)]])
        assert state.solo_victory_tier is None


class TestClubsAndSpadesPowers:
    def test_clubs_doubles_damage(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),  # immune to Hearts only
            hands=[[Card(Rank.EIGHT, Suit.CLUBS)]],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.EIGHT, Suit.CLUBS)))

        state.play_turn(decisions, random.Random(0))

        assert state.enemy.remaining_health == 20 - 16

    def test_spades_shield_reduces_the_same_turns_attack(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),  # attack 10, immune to Hearts only
            hands=[[Card(Rank.THREE, Suit.SPADES), Card(Rank.TEN, Suit.DIAMONDS)]],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.THREE, Suit.SPADES)))
        decisions.script_discard([Card(Rank.TEN, Suit.DIAMONDS)])

        state.play_turn(decisions, random.Random(0))

        assert state.enemy.shield == 3
        assert state.enemy.effective_attack == 7
        assert state.players[0].hand.is_empty

    def test_blocked_by_matching_enemy_immunity(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.CLUBS),  # immune to Clubs
            hands=[[Card(Rank.EIGHT, Suit.CLUBS)]],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.EIGHT, Suit.CLUBS)))

        state.play_turn(decisions, random.Random(0))

        assert state.enemy.remaining_health == 20 - 8  # not doubled
        assert state.enemy.shield == 10  # unaffected; equal to the pre-set neutralizing shield


class TestJester:
    def test_negates_immunity_skips_steps_three_and_four_and_picks_next_player(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.CLUBS),  # immune to Clubs
            hands=[[Card.jester()], [], []],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card.jester()))
        decisions.script_next_player(state.players[2])

        state.play_turn(decisions, random.Random(0))

        assert not state.enemy.is_suit_blocked(Suit.CLUBS)
        assert state.current_player is state.players[2]
        assert state.outcome is GameOutcome.IN_PROGRESS  # P1's empty hand never had to survive Step 4
        assert state.enemy.remaining_health == 20

    def test_can_choose_any_player_including_self(self):
        state = make_game(hands=[[Card.jester()], []])
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card.jester()))
        decisions.script_next_player(state.players[0])

        state.play_turn(decisions, random.Random(0))

        assert state.current_player is state.players[0]


class TestEnemyDefeatAndWin:
    def test_defeating_the_last_king_wins_and_places_it_facedown_on_tavern(self):
        state = make_game(
            enemy_card=Card(Rank.KING, Suit.DIAMONDS),  # health 40, immune to Diamonds only
            hands=[[Card(Rank.KING, Suit.CLUBS)]],  # 20 * 2 (Clubs) = exactly 40
            castle=[],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.KING, Suit.CLUBS)))

        state.play_turn(decisions, random.Random(0))

        assert state.outcome is GameOutcome.WON
        assert state.tavern.draw() == Card(Rank.KING, Suit.DIAMONDS)  # exact kill, facedown on top

    def test_overkill_defeat_discards_and_continues_same_player_against_next_enemy(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.DIAMONDS),  # health 20, immune to Diamonds only
            hands=[[Card(Rank.KING, Suit.CLUBS), Card(Rank.TWO, Suit.HEARTS)], []],
            castle=[Card(Rank.QUEEN, Suit.SPADES)],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.KING, Suit.CLUBS)))  # 20*2=40, overkill
        decisions.script_action(YIELD)  # same player's new turn against the Queen

        state.play_turn(decisions, random.Random(0))

        assert state.enemy.card == Card(Rank.QUEEN, Suit.SPADES)
        assert Card(Rank.JACK, Suit.DIAMONDS) in state.discard.cards
        assert Card(Rank.KING, Suit.CLUBS) in state.discard.cards
        # Queen's attack (15) exceeds the player's remaining hand value (2)
        assert state.outcome is GameOutcome.LOST


class TestGuards:
    def test_play_turn_raises_once_the_game_has_ended(self):
        state = make_game(hands=[[]])
        state.outcome = GameOutcome.WON
        with pytest.raises(ValueError):
            state.play_turn(ScriptedDecisions(), random.Random(0))


class TestNewGame:
    def test_deals_correct_hand_sizes_and_deck_composition(self):
        state = GameState.new_game(num_players=4, rng=random.Random(1))
        assert len(state.players) == 4
        assert all(player.hand.size == 5 for player in state.players)
        assert state.tavern.size == (9 * 4 + 4 + 2) - 4 * 5
        assert state.enemy.card.rank is Rank.JACK
        assert state.outcome is GameOutcome.IN_PROGRESS

    def test_deterministic_given_same_seed(self):
        first = GameState.new_game(3, random.Random(99))
        second = GameState.new_game(3, random.Random(99))
        assert [p.hand.cards for p in first.players] == [p.hand.cards for p in second.players]
        assert first.enemy.card == second.enemy.card


class TestObserverReporting:
    def _find(self, observer: RecordingObserver, name: str):
        return next(event for event in observer.events if event[0] == name)

    def test_yield_and_suffering_are_reported(self):
        state = make_game(
            hands=[[Card(Rank.TEN, Suit.SPADES)], [Card(Rank.TWO, Suit.HEARTS)]],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(YIELD)
        decisions.script_discard([Card(Rank.TEN, Suit.SPADES)])
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        assert [name for name, _ in observer.events] == ["on_yield", "on_player_suffered"]
        _, (yielder,) = observer.events[0]
        assert yielder is state.players[0]
        _, (sufferer, amount, discarded) = observer.events[1]
        assert sufferer is state.players[0]
        assert amount == 10
        assert discarded == (Card(Rank.TEN, Suit.SPADES),)

    def test_play_damage_and_shield_are_reported(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),
            hands=[[Card(Rank.SEVEN, Suit.SPADES)]],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        play = CardPlay.create(Card(Rank.SEVEN, Suit.SPADES))
        decisions.script_action(play)
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        _, (player, reported_play) = self._find(observer, "on_play")
        assert player is state.players[0]
        assert reported_play is play

        _, (enemy, amount, doubled) = self._find(observer, "on_damage_dealt")
        assert amount == 7
        assert not doubled

        _, (enemy, shield_amount) = self._find(observer, "on_shield_added")
        assert shield_amount == 7

    def test_hearts_reports_healed_count_when_not_blocked(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.SPADES),
            hands=[[Card(Rank.THREE, Suit.HEARTS)]],
            discard=[Card(Rank.FOUR, Suit.SPADES), Card(Rank.FIVE, Suit.DIAMONDS)],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.THREE, Suit.HEARTS)))
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        _, (healed, blocked) = self._find(observer, "on_hearts")
        assert healed == 2
        assert not blocked

    def test_hearts_reports_blocked_by_immunity(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.HEARTS),
            hands=[[Card(Rank.THREE, Suit.HEARTS)]],
            discard=[Card(Rank.FOUR, Suit.SPADES)],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.THREE, Suit.HEARTS)))
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        _, (healed, blocked) = self._find(observer, "on_hearts")
        assert healed == 0
        assert blocked

    def test_diamonds_reports_actual_drawn_count(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.SPADES),
            hands=[[Card(Rank.FOUR, Suit.DIAMONDS)]],
            tavern=[Card(Rank.FIVE, Suit.HEARTS), Card(Rank.SIX, Suit.HEARTS)],
            neutralize_attack=True,
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.FOUR, Suit.DIAMONDS)))
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        _, (drawn, blocked) = self._find(observer, "on_diamonds")
        assert drawn == 2  # only 2 cards were available, though 4 were requested
        assert not blocked

    def test_jester_reports_negated_immunity(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.CLUBS),
            hands=[[Card.jester()], []],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card.jester()))
        decisions.script_next_player(state.players[1])
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        assert [name for name, _ in observer.events] == ["on_play", "on_jester_negated_immunity"]

    def test_enemy_defeat_and_next_reveal_are_reported(self):
        state = make_game(
            enemy_card=Card(Rank.JACK, Suit.DIAMONDS),
            hands=[[Card(Rank.KING, Suit.CLUBS), Card(Rank.TWO, Suit.HEARTS)], []],
            castle=[Card(Rank.QUEEN, Suit.SPADES)],
        )
        decisions = ScriptedDecisions()
        decisions.script_action(CardPlay.create(Card(Rank.KING, Suit.CLUBS)))  # overkill: 40 dmg
        decisions.script_action(YIELD)
        observer = RecordingObserver()

        state.play_turn(decisions, random.Random(0), observer)

        _, (defeated_enemy, exact) = self._find(observer, "on_enemy_defeated")
        assert defeated_enemy.card == Card(Rank.JACK, Suit.DIAMONDS)
        assert not exact

        _, (revealed_enemy,) = self._find(observer, "on_enemy_revealed")
        assert revealed_enemy.card == Card(Rank.QUEEN, Suit.SPADES)
