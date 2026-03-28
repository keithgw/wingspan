# Wingspan RL

Reinforcement learning agents for the board game [Wingspan](https://stonemaiergames.com/games/wingspan/). The goal is to implement a simplified version of the game, then train agents to discover optimal play strategies through self-play — inspired by AlphaGo and Leela Chess Zero.

## Strategy

1. **Game engine** — Implement a playable simplified Wingspan (done)
2. **MCTS agent** — Monte Carlo Tree Search with UCT to learn action-value distributions (in progress)
3. **Self-play training** — Agents play against each other to iteratively improve their policies (future)

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
│   ├── entities/           # Core game objects
│   │   ├── bird.py         # Bird card (name, VP, food cost)
│   │   ├── birdfeeder.py   # Shared food supply (5 tokens, auto-reroll)
│   │   ├── deck.py         # Draw pile with shuffle
│   │   ├── food_supply.py  # Per-player food tokens
│   │   ├── gameboard.py    # Per-player board (5 bird slots)
│   │   ├── game_state.py   # Turn tracking, player rotation, game-over logic
│   │   ├── hand.py         # Player hand management
│   │   ├── player.py       # HumanPlayer (CLI) and BotPlayer (policy-driven)
│   │   └── tray.py         # Face-up bird display (3 slots)
│   ├── rl/
│   │   └── reinforcement_learning.py  # Policy ABC, RandomPolicy, State
│   ├── utilities/
│   │   └── utils.py        # Tabular rendering
│   └── game.py             # Game setup and play loop
├── tests/                  # 98 unit tests (unittest + pytest)
├── data/
│   ├── bird_data.csv       # Source bird data
│   ├── bird_list.py        # Generated: 180 Bird objects
│   └── generate_bird_list.py
```

## Getting Started

```bash
# Run tests
python -m pytest

# Play a game (2 bots, 10 turns each)
python -m src.game

# Play with a human player (2 players, 1 human)
python -m src.game 2 1
```

No external dependencies beyond pytest for testing.

## Architecture

### Game Engine
- **Players** inherit from a base `Player` class. `HumanPlayer` takes CLI input; `BotPlayer` delegates decisions to a `Policy` object
- **Game loop** rotates through players, validates legal actions, executes the chosen action, and updates state until turns are exhausted
- **Scoring** sums victory points of birds on each player's board

### RL Components
- **Policy** (ABC) maps game states to action probability distributions, with phase-specific methods for each decision point
- **RandomPolicy** provides a uniform random baseline
- **State** wraps the game state for policy consumption, tracking the current decision phase

### MCTS (in progress, branch `47-implement-basic-mcts`)
- **MCTSGameState** subclass with hashable `to_representation()` / `from_representation()` for game tree nodes
- **Expectimax** tree structure: decision nodes (player choices) and chance nodes (stochastic outcomes)
- **rhoUCT** outline for balancing exploration/exploitation with a stochastic environment model
- 26 commits ahead of main with state representation, player factory, and policy refactoring

## Open Issues

See [GitHub Issues](https://github.com/keithgw/wingspan/issues) for the full backlog. Key items:

- **#47** — Implement basic MCTS (core next milestone)
- **#53** — Refactor play loop for mid-turn simulation
- **#65** — Simplify Policy interface (remove phase dependency)
- **#55, #57, #58** — Improve state model with card memory
- **#19** — Turn zero draft decisions

## References

- [Expectimax MCTS (arXiv:0909.0801)](https://arxiv.org/abs/0909.0801) — Two node types for stochastic games
- [AlphaGo (Silver et al., 2016)](https://www.nature.com/articles/nature16961) — MCTS + neural network self-play
- [Wingspan (Stonemaier Games)](https://stonemaiergames.com/games/wingspan/)
