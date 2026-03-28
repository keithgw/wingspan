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
│   │   ├── policy.py     # Policy ABC, RandomPolicy, MCTSPolicy
│   │   └── mcts.py       # Node, Edge classes for game tree
│   ├── utilities/
│   │   ├── utils.py      # Terminal rendering helpers
│   │   └── player_factory.py  # Player creation (avoids circular imports)
│   └── game.py           # Game setup, turn loop, CLI entry point
├── tests/                # 157 unit tests (unittest + pytest)
├── data/                 # Bird data: 180 species from CSV, generated into bird_list.py
└── __init__.py
```

## Running
```bash
uv sync

# Run tests
uv run python -m pytest

# Play against random bot
uv run python -m src.game --num_players 2 --num_human 1

# Play against MCTS bot
uv run python -m src.game --num_players 2 --num_human 1 --policy mcts

# Stronger MCTS (more simulations, slower)
uv run python -m src.game --num_players 2 --num_human 1 --policy mcts --num_simulations 500
```

## Architecture Notes
- **GameState** consolidates all game objects: bird_deck, discard_pile, tray, bird_feeder, players, phase
- **MCTSGameState** extends GameState with `to_representation()`/`from_representation()` for hashable state serialization (determinizes hidden info for imperfect-information MCTS)
- **Players**: `HumanPlayer` (CLI) and `BotPlayer` (policy-driven) inherit from `Player`
- **Policies**: `Policy.__call__(state, actions) → str`. `RandomPolicy` picks uniformly. `MCTSPolicy` runs full select → expand → playout → backpropagate loop with UCB1 tree policy
- **Actions**: 3 of 4 implemented: play_a_bird, gain_food, draw_a_bird. Lay eggs NOT implemented
- **Simplifications**: Birds only have VP and food cost (no habitats, egg capacity, or powers). Single food type. No bonus cards or end-of-round goals
- **Entity serialization**: All entities have `to_representation()` returning hashable types; BirdHand, GameBoard, Tray have `from_representation()` for reconstruction

## Next Milestone
Self-play training framework (#74): run bot-vs-bot games, collect experience, train policies, persist for reuse. Then learned playout policy (#73) and value network (#75).

## Conventions
- Python unittest framework, run with pytest
- `pyproject.toml` manages dependencies via uv; runtime dep: `numpy`, dev deps: `pytest`, `ruff`, `pre-commit`
- `hatchling` build backend; `src` and `data` are the package directories
- Ruff for linting (E/F/I/UP rules) and formatting (line-length 120)
- Pre-commit hooks run ruff on commit; CI runs lint + tests on push/PR to main
- Test files mirror source structure in tests/ directory
- Internal methods prefixed with `_`; public API is the unprefixed methods
