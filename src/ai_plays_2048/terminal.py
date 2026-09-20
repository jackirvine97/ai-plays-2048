"""A small terminal renderer; tmux is simply one way to host it."""

from __future__ import annotations

from .engine import Board, Direction, Game


def render(board: Board, score: int = 0) -> str:
    width = max(5, len(str(board.highest_tile)))
    rule = "+" + "+".join("-" * (width + 2) for _ in range(board.size)) + "+"
    rows = [f"2048  score: {score}", rule]
    for line in board.cells:
        rows.append("|" + "|".join(f"{value or '':^{width + 2}}" for value in line) + "|")
        rows.append(rule)
    rows.append("Use arrow keys/WASD. q quits; r starts a new game.")
    return "\n".join(rows)


def play() -> None:
    """Run a deliberately dependency-free, line-command playable frontend."""
    game = Game()
    keys = {"w": Direction.UP, "a": Direction.LEFT, "s": Direction.DOWN, "d": Direction.RIGHT,
            "up": Direction.UP, "left": Direction.LEFT, "down": Direction.DOWN, "right": Direction.RIGHT}
    while True:
        print("\033[2J\033[H" + render(game.board, game.score), flush=True)
        if game.is_over:
            print("Game over. Press r to restart or q to quit.")
        elif game.is_won:
            print("You reached 2048. Continue playing, restart, or quit.")
        key = input("> ").strip().lower()
        if key == "q":
            return
        if key == "r":
            game.reset()
        elif key in keys and not game.is_over:
            game.move(keys[key])
