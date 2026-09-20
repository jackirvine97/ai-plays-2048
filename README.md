# ai-plays-2048

A common, deterministic 2048 rules engine for comparing different players.
The engine does not know about terminals, tmux, or models; those are adapters
on top of the same `Game` API.

## Setup

```bash
uv sync --all-groups --extra llm --extra jev
```

## Play in tmux

```bash
uv run ai-plays-2048 tmux --session ai-2048
tmux attach -t ai-2048
```

Inside the game use `W`, `A`, `S`, `D` (or direction names), `r` to restart,
and `q` to quit. The shell frontend is intentionally simple so it is reliable
inside tmux and easy to replace later with a richer renderer.

## Run the initial LLM player

```bash
export OPENAI_API_KEY=...
uv run --extra llm ai-plays-2048 llm --model openai:gpt-4.1-mini
```

It ports the original experiment's structured game-state reading, one-move
tool use, restart loop, persistent strategic memory, and explicit victory
check. Unlike the original, its tools operate on the shared engine directly,
so it never has to infer a board by scraping a tmux pane. Its memory defaults
to `.ai-plays-2048/memory.json` and is intentionally ignored by Git.

## Add another player

Implement an adapter that owns a `Game` and chooses from `Direction`. Do not
put strategy, terminal handling, or model dependencies in `engine.py`.

```python
from ai_plays_2048 import Direction, Game

game = Game(seed=42)
result = game.move(Direction.LEFT)
```

## Run the Jev typed-decision player

Copy `.env.example` to `.env`, add `TYPESAFE_API_KEY`, then run:

```bash
uv run --extra jev ai-plays-2048 jev --seed 42
```

Jev receives the rendered board and the engine-supplied legal move list each
turn. Its Pydantic return model only permits the four directions; the adapter
also refuses a direction that is not legal on the current board. This gives us
a short, inspectable type-safe policy loop to compare with the generative LLM
player.

## Verify

```bash
uv run --group dev pytest
```
