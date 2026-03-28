# Wingspan RL

Reinforcement learning agents for the board game [Wingspan](https://stonemaiergames.com/games/wingspan/). The goal is to implement a simplified version of the game, then train agents to discover optimal play strategies through self-play — inspired by AlphaGo and Leela Chess Zero.

## Strategy

1. **Game engine** — Implement a playable simplified Wingspan (done)
2. **MCTS agent** — Monte Carlo Tree Search with UCT to select actions (done)
3. **Self-play training** — Agents play against each other to iteratively improve their policies (next)

## Playing the Game

```bash
# Install uv if you don't have it
# https://docs.astral.sh/uv/getting-started/installation/

# Sync dependencies (creates .venv automatically)
uv sync

# Play against a random bot
uv run python -m src.game --num_players 2 --num_human 1

# Play against an MCTS bot (smarter, ~0.2s per decision)
uv run python -m src.game --num_players 2 --num_human 1 --policy mcts

# Crank up MCTS simulations for stronger play
uv run python -m src.game --num_players 2 --num_human 1 --policy mcts --num_simulations 500

# Watch two bots play each other
uv run python -m src.game

# Run tests
uv run python -m pytest
```

## Game Simplifications

The game engine implements a subset of Wingspan's rules:

| Feature | Real Wingspan | This Implementation |
|---------|--------------|---------------------|
| Bird cards | 170+ unique birds with powers | 180 birds, VP + food cost only (no powers) |
| Food types | 5 distinct types | Single generic food token |
| Actions | 4 (play bird, gain food, lay eggs, draw bird) | 3 (no lay eggs) |
| Habitats | 3 rows with increasing capacity | Single flat board (5 slots) |
| Bonus cards | End-of-round and end-of-game goals | Not implemented |
| Egg mechanic | Eggs as resources and VP | Not implemented |

These simplifications reduce the state space to make MCTS tractable while preserving the core decision-making loop: which birds to play, when to gather resources, and when to invest in drawing new options.

## Project Structure

```
wingspan/
├── src/
│   ├── constants.py        # Game phase constants
│   ├── entities/           # Core game objects
│   │   ├── bird.py         # Bird card (name, VP, food cost)
│   │   ├── birdfeeder.py   # Shared food supply (5 tokens, auto-reroll)
│   │   ├── deck.py         # Draw pile with shuffle
│   │   ├── food_supply.py  # Per-player food tokens
│   │   ├── gameboard.py    # Per-player board (5 bird slots)
│   │   ├── game_state.py   # GameState + MCTSGameState (serialization)
│   │   ├── hand.py         # Player hand management
│   │   ├── player.py       # Player, HumanPlayer (CLI), BotPlayer (policy-driven)
│   │   └── tray.py         # Face-up bird display (3 slots)
│   ├── rl/
│   │   ├── policy.py       # Policy ABC, RandomPolicy, MCTSPolicy
│   │   └── mcts.py         # Node and Edge classes for game tree
│   ├── utilities/
│   │   ├── utils.py        # Terminal rendering helpers
│   │   └── player_factory.py  # Player creation (avoids circular imports)
│   └── game.py             # Game setup, turn loop, CLI entry point
├── tests/                  # 157 unit tests (unittest + pytest)
├── data/
│   ├── bird_data.csv       # Source bird data
│   ├── bird_list.py        # Generated: 180 Bird objects
│   └── generate_bird_list.py
```

## Architecture

### Game Engine
- **GameState** consolidates all game objects: bird deck, discard pile, tray, bird feeder, players, and turn/phase tracking
- **Players** inherit from `Player`. `HumanPlayer` takes CLI input; `BotPlayer` delegates decisions to a `Policy` object
- **Game loop** rotates through players, validates legal actions, executes the chosen action, and updates state until turns are exhausted
- **Scoring** sums victory points of birds on each player's board

### RL / MCTS
- **Policy** maps `(state, actions) → chosen action`. `RandomPolicy` picks uniformly; `MCTSPolicy` uses tree search
- **MCTSPolicy** implements the full select → expand → playout → backpropagate loop:
  - **Select**: traverse the tree via UCB1 to find a leaf node
  - **Expand**: generate child nodes for each legal action (using `copy.deepcopy`)
  - **Playout**: simulate the game to completion using `RandomPolicy` (cloned via `MCTSGameState.from_representation` for imperfect-information determinization)
  - **Backpropagate**: walk parent pointers updating visit counts and rewards
- **MCTSGameState** extends GameState with hashable `to_representation()` / `from_representation()` for state serialization, handling hidden information (opponent hands stored as counts)

## Roadmap

See [GitHub Issues](https://github.com/keithgw/wingspan/issues) for the full backlog. Next milestones:

- **#74** — Self-play training framework with policy persistence
- **#73** — Replace random playout policy with a learned policy
- **#75** — Add a value network to evaluate positions without full playout

## References

- [Expectimax MCTS (arXiv:0909.0801)](https://arxiv.org/abs/0909.0801) — Two node types for stochastic games
- [AlphaGo (Silver et al., 2016)](https://www.nature.com/articles/nature16961) — MCTS + neural network self-play
- [Wingspan (Stonemaier Games)](https://stonemaiergames.com/games/wingspan/)
