from __future__ import annotations

from dataclasses import asdict, dataclass

from regicide.cards import Card
from regicide.game_state import GameState
from regicide.player import Player


@dataclass(frozen=True)
class PlayerView:
    name: str
    hand_size: int


@dataclass(frozen=True)
class EnemyView:
    card: str
    health: int
    remaining_health: int
    attack: int
    effective_attack: int
    shield: int
    immunity_negated: bool


@dataclass(frozen=True)
class GameView:
    current_player: str
    hand: tuple[str, ...]
    enemy: EnemyView
    cards_in_play: tuple[str, ...]
    tavern_size: int
    discard: tuple[str, ...]
    players: tuple[PlayerView, ...]
    castle_size: int
    can_yield: bool
    solo_jesters_remaining: int | None

    @classmethod
    def for_player(cls, player: Player, state: GameState) -> GameView:
        if player not in state.players:
            raise ValueError(f"{player.name} is not seated in this game")

        enemy = state.enemy
        return cls(
            current_player=player.name,
            hand=tuple(_card_id(card) for card in player.hand.cards),
            enemy=EnemyView(
                card=_card_id(enemy.card),
                health=enemy.health,
                remaining_health=enemy.remaining_health,
                attack=enemy.attack,
                effective_attack=enemy.effective_attack,
                shield=enemy.shield,
                immunity_negated=enemy.immunity_negated,
            ),
            cards_in_play=tuple(_card_id(card) for card in state.cards_in_play),
            tavern_size=state.tavern.size,
            discard=tuple(_card_id(card) for card in state.discard.cards),
            players=tuple(PlayerView(p.name, p.hand.size) for p in state.players),
            castle_size=state.castle.size,
            can_yield=player is state.current_player and state.turn_order.can_yield(),
            solo_jesters_remaining=(
                state.solo_jesters.remaining if state.solo_jesters is not None else None
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _card_id(card: Card) -> str:
    return str(card)
