import contextlib
import io

import numpy as np

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_ACTION


class Policy:
    def __call__(self, state, actions):
        if state.phase == CHOOSE_ACTION:
            return self._policy_choose_action(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return self._policy_choose_a_bird_to_play(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            return self._policy_choose_a_bird_to_draw(state, actions)

    def _policy_choose_action(self, state, legal_actions):
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        raise NotImplementedError


class RandomPolicy(Policy):
    def _uniform_random_choice(self, actions):
        """Return a choice uniformly at random from the list of actions."""
        return np.random.choice(actions)

    def _policy_choose_action(self, state, legal_actions):
        return self._uniform_random_choice(legal_actions)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._uniform_random_choice(playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._uniform_random_choice(valid_choices)


class MCTSPolicy(Policy):
    def __init__(self, num_simulations=1000):
        super().__init__()
        self.num_simulations = num_simulations
        self.root = None
        self._mcts_player_index = None

    def _rhoUCT(self, state, actions):
        """UCT with environment model (rho). Returns max_a[Q(s, a)]."""
        from src.entities.game_state import MCTSGameState
        from src.rl.mcts import Node

        mcts_state = MCTSGameState.from_game_state(state)
        root = Node(state=mcts_state)

        # Track which player we're optimizing for
        self._mcts_player_index = state.game_turn % state.num_players

        # TODO: implement subtree reuse by comparing state representations
        # (requires Node.__eq__/__hash__ based on state.to_representation())

        # Run simulations to estimate action values
        self._run_simulations(root, self.num_simulations)

        # Choose the most-visited child
        best_child = self._best_child(root)
        best_action = best_child.action

        assert best_action in actions, f"Chosen action must be one of {actions}, but was {best_action}."
        return best_action

    def _policy_choose_action(self, state, legal_actions):
        return self._rhoUCT(state=state, actions=legal_actions)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._rhoUCT(state=state, actions=playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._rhoUCT(state=state, actions=valid_choices)

    def _select_child(self, node):
        """Tree policy: select child with highest UCB1."""
        return max(node.children, key=lambda child: child.get_ucb1())

    def _select_leaf(self, root):
        """Traverse the tree until reaching a leaf node."""
        node = root
        while node.children:
            node = self._select_child(node)
        return node

    def _expand(self, leaf):
        """Expand the leaf node by generating children."""
        raise NotImplementedError

    def _playout(self, node):
        """Simulate a game from this node to completion using random play."""
        from src.entities.game_state import MCTSGameState

        # Clone state via determinization (creates BotPlayers with RandomPolicy)
        sim_state = MCTSGameState.from_representation(node.state.to_representation())

        with contextlib.redirect_stdout(io.StringIO()):
            # Complete mid-turn action if needed
            current_player = sim_state.get_current_player()
            if sim_state.phase == CHOOSE_A_BIRD_TO_PLAY:
                current_player.play_a_bird(sim_state)
                sim_state.end_player_turn(player=current_player)
            elif sim_state.phase == CHOOSE_A_BIRD_TO_DRAW:
                current_player.draw_a_bird(sim_state)
                sim_state.end_player_turn(player=current_player)

            # Run game to completion
            while not sim_state.is_game_over():
                current_player = sim_state.get_current_player()
                action = current_player.request_action(game_state=sim_state)
                current_player.take_action(action=action, game_state=sim_state)
                sim_state.end_player_turn(player=current_player)

        return self._compute_reward(sim_state)

    def _compute_reward(self, sim_state):
        """Compute reward from the MCTS player's perspective. Returns 1.0/0.5/0.0."""
        scores = [player.get_score() for player in sim_state.get_players()]
        mcts_score = scores[self._mcts_player_index]
        max_score = max(scores)

        if mcts_score < max_score:
            return 0.0

        num_winners = sum(1 for s in scores if s == max_score)
        return 1.0 if num_winners == 1 else 0.5

    def _backpropagate(self, node, reward):
        """Propagate reward up the tree."""
        raise NotImplementedError

    def _run_simulations(self, root, num_simulations):
        for _ in range(num_simulations):
            leaf = self._select_leaf(root)
            unexplored_node = self._expand(leaf)
            reward = self._playout(unexplored_node)
            self._backpropagate(unexplored_node, reward)

    def _best_child(self, node):
        """Choose the child with the highest visit count."""
        return max(node.children, key=lambda child: child.num_visits)
