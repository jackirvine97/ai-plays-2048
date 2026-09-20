from __future__ import annotations

import argparse
import subprocess
import sys

from .terminal import play


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared 2048 engine and player playground")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("play", help="Play 2048 in this terminal")
    tmux = commands.add_parser("tmux", help="Start a detachable terminal game")
    tmux.add_argument("--session", default="ai-2048")
    llm = commands.add_parser("llm", help="Run the tool-calling LangChain player")
    llm.add_argument("--model", required=True, help="e.g. openai:gpt-4.1-mini")
    llm.add_argument("--memory", default=".ai-plays-2048/memory.json")
    jev = commands.add_parser("jev", help="Run the type-safe Jev decision player")
    jev.add_argument("--seed", type=int)
    jev.add_argument("--max-moves", type=int, default=10_000)
    jev.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.command == "play":
        play()
    elif args.command == "tmux":
        command = f"{sys.executable} -m ai_plays_2048 play"
        subprocess.run(["tmux", "new-session", "-A", "-s", args.session, command], check=True)
    elif args.command == "llm":
        from pathlib import Path
        from .llm.app import run
        won = run(args.model, memory_path=Path(args.memory))
        raise SystemExit(0 if won else 1)
    elif args.command == "jev":
        from .jev.app import run
        game = run(seed=args.seed, max_moves=args.max_moves, show_board=not args.quiet)
        raise SystemExit(0 if game.is_won else 1)
