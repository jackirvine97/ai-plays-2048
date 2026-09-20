"""A type-safe Jev policy that plays the shared 2048 engine."""

from typing import Callable, Literal

from ..engine import Direction, Game
from ..terminal import render


def _imports():
    try:
        import jev
        from pydantic import BaseModel, Field
    except ImportError as error:
        raise RuntimeError("Install the Jev extra: uv sync --extra jev") from error
    return jev, BaseModel, Field


def build_policy() -> Callable[[str, tuple[str, ...], int], Direction]:
    """Build a Jev query whose response is schema-validated before every move."""
    jev, BaseModel, Field = _imports()

    class MoveDecision(BaseModel):
        direction: Literal["up", "down", "left", "right"] = Field(
            description="Choose exactly one direction listed in legal_moves. Prefer preserving a monotonic corner and moves that create space."
        )

    @jev.fn
    def choose_move(board: str, legal_moves: tuple[str, ...], target: int) -> MoveDecision:
        """Choose the strongest next move in this game of 2048.

        Board:
        {{ board }}

        legal_moves (you MUST choose one of these): {{ legal_moves }}
        Target tile: {{ target }}
        """
        return choose_move.state()

    def policy(board: str, legal_moves: tuple[str, ...], target: int) -> Direction:
        decision = choose_move(board, legal_moves, target)
        direction = Direction(decision.direction)
        # Jev's response is type-safe; this guard also protects the engine if a
        # valid direction is unsuitable for this particular board.
        return direction if direction.value in legal_moves else Direction(legal_moves[0])

    return policy


def run(*, seed: int | None = None, max_moves: int = 10_000, show_board: bool = True) -> Game:
    """Play one bounded game, selecting every move through a typed Jev decision."""
    game = Game(seed=seed)
    policy = build_policy()
    while not game.is_over and not game.is_won and game.moves < max_moves:
        legal_moves = tuple(move.value for move in game.board.legal_moves())
        direction = policy(render(game.board, game.score), legal_moves, game.target)
        result = game.move(direction)
        if show_board:
            print(render(game.board, game.score))
            print(f"Jev chose {direction.value}; +{result.score_gained} points\n")
    if show_board:
        status = "won" if game.is_won else "lost" if game.is_over else "move limit reached"
        print(f"Jev {status}: {game.moves} moves, score {game.score}, highest tile {game.board.highest_tile}.")
    return game
