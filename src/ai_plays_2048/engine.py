"""Deterministic, UI-free rules for the 4×4 game 2048."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Iterable, Optional, Sequence, Union


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True)
class Board:
    """An immutable square board. Zero represents an empty cell."""

    cells: tuple[tuple[int, ...], ...]

    def __post_init__(self) -> None:
        size = len(self.cells)
        if size < 2 or any(len(row) != size for row in self.cells):
            raise ValueError("Board must be a square of at least 2×2 cells")
        if any(value < 0 or (value and value & (value - 1)) for row in self.cells for value in row):
            raise ValueError("Cells must contain zero or a positive power of two")

    @classmethod
    def empty(cls, size: int = 4) -> "Board":
        return cls(tuple((0,) * size for _ in range(size)))

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[int]]) -> "Board":
        return cls(tuple(tuple(row) for row in rows))

    @property
    def size(self) -> int:
        return len(self.cells)

    @property
    def highest_tile(self) -> int:
        return max(value for row in self.cells for value in row)

    @property
    def empty_positions(self) -> tuple[tuple[int, int], ...]:
        return tuple((row, col) for row, line in enumerate(self.cells) for col, value in enumerate(line) if value == 0)

    def _lines_for(self, direction: Direction) -> Iterable[tuple[int, ...]]:
        n = self.size
        if direction is Direction.LEFT:
            yield from self.cells
        elif direction is Direction.RIGHT:
            yield from (tuple(reversed(row)) for row in self.cells)
        elif direction is Direction.UP:
            yield from (tuple(self.cells[row][col] for row in range(n)) for col in range(n))
        else:
            yield from (tuple(self.cells[row][col] for row in reversed(range(n))) for col in range(n))

    def move(self, direction: Direction) -> tuple["Board", int, bool]:
        """Return the moved board, points earned, and whether anything changed."""
        moved_lines: list[tuple[int, ...]] = []
        gained = 0
        for line in self._lines_for(direction):
            values = [value for value in line if value]
            result: list[int] = []
            index = 0
            while index < len(values):
                if index + 1 < len(values) and values[index] == values[index + 1]:
                    merged = values[index] * 2
                    result.append(merged)
                    gained += merged
                    index += 2
                else:
                    result.append(values[index])
                    index += 1
            moved_lines.append(tuple(result + [0] * (self.size - len(result))))

        n = self.size
        target = [[0] * n for _ in range(n)]
        for line_index, line in enumerate(moved_lines):
            for cell_index, value in enumerate(line):
                if direction is Direction.LEFT:
                    row, col = line_index, cell_index
                elif direction is Direction.RIGHT:
                    row, col = line_index, n - 1 - cell_index
                elif direction is Direction.UP:
                    row, col = cell_index, line_index
                else:
                    row, col = n - 1 - cell_index, line_index
                target[row][col] = value
        board = Board.from_rows(target)
        return board, gained, board != self

    def legal_moves(self) -> tuple[Direction, ...]:
        return tuple(direction for direction in Direction if self.move(direction)[2])


@dataclass(frozen=True)
class MoveResult:
    direction: Direction
    changed: bool
    score_gained: int
    spawned: Optional[tuple[int, int, int]]
    score: int
    game_over: bool
    won: bool


class Game:
    """A mutable game session built on :class:`Board`, with injectable randomness."""

    def __init__(self, *, size: int = 4, target: int = 2048, seed: Optional[int] = None) -> None:
        self.size, self.target, self.seed = size, target, seed
        self._random = Random(seed)
        self.reset()

    def reset(self) -> Board:
        self._random = Random(self.seed)
        self.board = Board.empty(self.size)
        self.score = 0
        self.moves = 0
        self._spawn_tile()
        self._spawn_tile()
        return self.board

    def _spawn_tile(self) -> Optional[tuple[int, int, int]]:
        positions = self.board.empty_positions
        if not positions:
            return None
        row, col = self._random.choice(positions)
        value = 4 if self._random.random() < 0.1 else 2
        rows = [list(line) for line in self.board.cells]
        rows[row][col] = value
        self.board = Board.from_rows(rows)
        return row, col, value

    @property
    def is_over(self) -> bool:
        return not self.board.legal_moves()

    @property
    def is_won(self) -> bool:
        return self.board.highest_tile >= self.target

    def move(self, direction: Union[Direction, str]) -> MoveResult:
        direction = Direction(direction)
        moved, gained, changed = self.board.move(direction)
        spawned = None
        if changed:
            self.board = moved
            self.score += gained
            self.moves += 1
            spawned = self._spawn_tile()
        return MoveResult(direction, changed, gained, spawned, self.score, self.is_over, self.is_won)
