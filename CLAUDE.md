# Wingspan RL Project

## Overview
Reinforcement learning agents for the board game Wingspan. The strategy is to:
1. Implement a simplified version of Wingspan as a game engine
2. Implement learning algorithms (MCTS, then self-play) to discover optimal play policies
3. Let agents play against each other and learn, similar to AlphaGo/Leela approaches

## Project Structure
```
wingspan/
├── src/
│   ├── entities/         # Core game components (bird, deck, player, board, etc.)
│   ├── rl/               # RL components (policy.py on MCTS branch, reinforcement_learning.py on main)
│   ├── utilities/        # Rendering helpers
│   └── game.py           # Main game loop orchestration
├── tests/                # unittest-based test suite (98 tests, all passing on main)
├── data/                 # Bird data: 180 species from CSV, generated into bird_list.py
└── __init__.py
```

## Running
```bash
# Sync dependencies (creates .venv)
uv sync

# Run tests
uv run python -m pytest

# Run a game (from repo root)
uv run python -m src.game                           # default: 2 bots, 10 turns each
uv run python -m src.game --num_players 2 --num_human 1      # 2 players, 1 human
```

## Key Branches
- `main` — stable game engine with RandomPolicy
- `origin/47-implement-basic-mcts` — WIP MCTS implementation (26 commits ahead of main), includes state representation, MCTSGameState, player factory, rhoUCT outline

## Architecture Notes
- **Players**: `HumanPlayer` (CLI input) and `BotPlayer` (policy-driven) inherit from `Player`
- **Policies**: Abstract `Policy` base class; `RandomPolicy` implemented. MCTS branch outlines `rhoUCT`
- **Actions**: 3 of 4 actions implemented: play_a_bird, gain_food, draw_a_bird. Lay eggs NOT implemented
- **Simplifications**: Birds only have VP and food cost (no habitats, egg capacity, or special powers). Food is a single token type (real game has 5 types). No bonus cards, no end-of-round goals
- **State representation**: MCTS branch adds `to_representation()` / `from_representation()` for hashable state vectors

## Conventions
- Python unittest framework, run with pytest
- `pyproject.toml` manages dependencies via uv; runtime dep: `numpy`, dev dep: `pytest`
- `hatchling` build backend; `src` and `data` are the package directories
- Test files mirror source structure in tests/ directory
