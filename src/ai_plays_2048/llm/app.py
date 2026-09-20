"""LangChain player adapter for the shared in-process 2048 engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ..engine import Direction, Game

SYSTEM_PROMPT = """You are an autonomous 2048 player. Reach the target tile. Use read_game_state before decisions and make one move at a time. Keep the largest tile in a stable corner, avoid moves that undo that structure, and use your memory only for durable strategy—not a move-by-move journal. When the game is over, start a new one and retain only useful lessons. Call declare_victory only after read_game_state confirms a tile at least as large as the target."""


class MemoryStore:
    """Small, inspectable long-term memory shared across LLM attempts."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, str]:
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def write(self, values: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n")


class LLMPlayer:
    """Expose one Game to a model as narrow, deterministic tools."""

    def __init__(self, game: Optional[Game] = None, memory_path: Optional[Path] = None) -> None:
        self.game = game or Game()
        self.memory = MemoryStore(memory_path or Path(".ai-plays-2048/memory.json"))
        self.declared_victory = False

    def state(self) -> dict[str, Any]:
        return {"board": [list(row) for row in self.game.board.cells], "score": self.game.score, "moves": self.game.moves, "highest_tile": self.game.board.highest_tile, "target": self.game.target, "legal_moves": [move.value for move in self.game.board.legal_moves()], "game_over": self.game.is_over, "won": self.game.is_won}

    def tools(self) -> list[Any]:
        """Create tools lazily so the core package has no LangChain dependency."""
        try:
            from langchain.tools import tool
        except ImportError as error:
            raise RuntimeError("Install the LLM extra: uv sync --extra llm") from error

        @tool
        def read_game_state() -> dict[str, Any]:
            """Read the exact board, score, status, and currently legal moves."""
            return self.state()

        @tool
        def make_move(direction: str) -> dict[str, Any]:
            """Make exactly one legal move: up, down, left, or right."""
            try:
                result = self.game.move(Direction(direction.lower()))
            except ValueError:
                return {"error": "direction must be one of up, down, left, right"}
            return {"changed": result.changed, "score_gained": result.score_gained, "spawned": result.spawned, **self.state()}

        @tool
        def restart_game() -> dict[str, Any]:
            """Start a fresh game after a loss; long-term memory is retained."""
            self.game.reset()
            return self.state()

        @tool
        def read_memory() -> dict[str, str]:
            """Read distilled strategic lessons from earlier games."""
            return self.memory.read()

        @tool
        def save_memory(memory_id: str, lesson: str) -> str:
            """Create or replace one concise, durable strategic lesson."""
            values = self.memory.read()
            values[memory_id] = lesson
            self.memory.write(values)
            return f"Saved memory {memory_id}."

        @tool
        def delete_memory(memory_id: str) -> str:
            """Remove a stale or redundant strategic lesson."""
            values = self.memory.read()
            if memory_id not in values:
                return f"Memory {memory_id} does not exist."
            del values[memory_id]
            self.memory.write(values)
            return f"Deleted memory {memory_id}."

        @tool
        def declare_victory() -> str:
            """Use only after the board contains the target tile."""
            if not self.game.is_won:
                return "Victory cannot be declared: target tile is not present."
            self.declared_victory = True
            return "Victory confirmed."

        return [read_game_state, make_move, restart_game, read_memory, save_memory, delete_memory, declare_victory]


def run(model: str, *, memory_path: Optional[Path] = None) -> bool:
    """Run until victory; a fresh prompt follows any model turn that stops early."""
    try:
        from langchain.agents import create_agent
        from langchain.chat_models import init_chat_model
    except ImportError as error:
        raise RuntimeError("Install the LLM extra: uv sync --extra llm") from error
    player = LLMPlayer(memory_path=memory_path)
    agent = create_agent(model=init_chat_model(model), tools=player.tools(), system_prompt=SYSTEM_PROMPT)
    prompt = "Play 2048 until you win. Do not stop before declaring verified victory."
    while not player.declared_victory:
        for _ in agent.stream({"messages": [{"role": "user", "content": prompt}]}, stream_mode="updates"):
            if player.declared_victory:
                return True
        prompt = "You stopped without winning. Read the state and continue playing until verified victory."
    return True
