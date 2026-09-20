from ai_plays_2048.engine import Board, Direction, Game


def test_a_tile_merges_only_once_per_move() -> None:
    board = Board.from_rows([[2, 2, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    moved, score, changed = board.move(Direction.LEFT)
    assert moved.cells[0] == (4, 4, 0, 0)
    assert score == 8
    assert changed


def test_move_does_not_spawn_when_it_changes_nothing() -> None:
    game = Game(seed=7)
    game.board = Board.from_rows([[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    result = game.move("left")
    assert not result.changed
    assert result.spawned is None
    assert game.moves == 0


def test_game_is_over_when_full_without_adjacent_equals() -> None:
    game = Game(seed=1)
    game.board = Board.from_rows([[2, 4, 2, 4], [4, 2, 4, 2], [2, 4, 2, 4], [4, 2, 4, 2]])
    assert game.is_over
