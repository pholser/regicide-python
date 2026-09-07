from __future__ import annotations

from regicide.cards import Card
from regicide.decks import DiscardPile, TavernDeck
from regicide.enemy import AttackResult, Enemy
from regicide.play import CardPlay


class Encounter:
    """A fight against one enemy: the enemy itself plus the cards played
    against it so far. The rules track "cards played against this enemy"
    as a unit tied to that specific fight -- both are cleared together the
    moment the enemy is defeated -- so they live together here rather than
    as two separately-managed pieces of state.
    """

    def __init__(self, enemy: Enemy) -> None:
        self.enemy = enemy
        self.cards_in_play: list[Card] = []

    def negate_immunity(self) -> None:
        self.enemy.negate_immunity()

    def record_play(self, play: CardPlay) -> None:
        self.cards_in_play.extend(play.cards)

    def resolve_play(self, play: CardPlay) -> AttackResult:
        """Record the play and let the enemy react to it (Step 3)."""
        self.record_play(play)
        return self.enemy.resolve_play(play)

    def defeat(self, tavern: TavernDeck, discard: DiscardPile) -> None:
        """Clean up once the enemy is defeated: an exact kill goes facedown
        on top of the Tavern deck; otherwise it joins the discard pile
        along with every card played against it this fight."""
        to_discard = self.cards_in_play
        self.cards_in_play = []
        if self.enemy.is_exactly_defeated:
            tavern.place_on_top([self.enemy.card])
        else:
            to_discard.append(self.enemy.card)
        discard.add_all(to_discard)
