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
│   ├── constants.py      # Game phase constants
│   ├── entities/         # Core game components (bird, deck, player, board, etc.)
│   ├── rl/
│   │   ├── policy.py     # Policy ABC, RandomPolicy, MCTSPolicy (stubs)
│   │   └── mcts.py       # Node, Edge classes for game tree
│   ├── utilities/
│   │   ├── utils.py      # Rendering helpers
│   │   └── player_factory.py  # Player creation (avoids circular imports)
│   └── game.py           # Main game loop orchestration
├── tests/                # unittest-based test suite (134 tests)
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

## Architecture Notes
- **GameState** consolidates all game objects: bird_deck, discard_pile, tray, bird_feeder, players, phase
- **MCTSGameState** extends GameState with `to_representation()`/`from_representation()` for hashable state serialization
- **Players**: `HumanPlayer` (CLI input) and `BotPlayer` (policy-driven) inherit from `Player`
- **Policies**: `Policy.__call__(state, actions) → str`. `RandomPolicy` picks uniformly. `MCTSPolicy` has rhoUCT scaffold (expand/playout/backpropagate are stubs)
- **Actions**: 3 of 4 actions implemented: play_a_bird, gain_food, draw_a_bird. Lay eggs NOT implemented
- **Simplifications**: Birds only have VP and food cost (no habitats, egg capacity, or special powers). Food is a single token type (real game has 5 types). No bonus cards, no end-of-round goals
- **Entity serialization**: All entities have `to_representation()` returning hashable types; BirdHand, GameBoard, Tray have `from_representation()` for reconstruction

## MCTS Development Frontier
The `MCTSPolicy._expand()`, `._playout()`, and `._backpropagate()` methods are stubs. These are the next pieces to implement. Key design decisions (from issue #47):
- Expectimax tree: decision nodes (player choices) and chance nodes (stochastic outcomes)
- Handle stochasticity via simulation, not enumeration
- rhoUCT = UCT + environment model

## Conventions
- Python unittest framework, run with pytest
- `pyproject.toml` manages dependencies via uv; runtime dep: `numpy`, dev deps: `pytest`, `ruff`, `pre-commit`
- `hatchling` build backend; `src` and `data` are the package directories
- Ruff for linting (E/F/I/UP rules) and formatting (line-length 120)
- Pre-commit hooks run ruff on commit; CI runs lint + tests on push/PR to main
- Test files mirror source structure in tests/ directory
