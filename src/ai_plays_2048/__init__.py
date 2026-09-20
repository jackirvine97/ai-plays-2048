"""Shared 2048 engine plus human and AI player frontends."""

from .engine import Board, Direction, Game, MoveResult

__all__ = ["Board", "Direction", "Game", "MoveResult"]


def main() -> None:
    from .cli import main as cli_main

    cli_main()
