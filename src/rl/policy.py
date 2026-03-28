import contextlib
import copy
import io

import numpy as np

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_ACTION


class Policy:
    """Abstract base for policies that map (state, actions) to a chosen action string.

    Dispatches to phase-specific methods based on state.phase. Subclasses must
    implement _policy_choose_action, _policy_choose_a_bird_to_play, and
    _policy_choose_a_bird_to_draw.
    """

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
    """Policy that selects uniformly at random from legal actions."""

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
    """Policy that uses Monte Carlo Tree Search (rhoUCT) to select actions.

    Builds a game tree via repeated select-expand-playout-backpropagate cycles,
    then returns the action leading to the most-visited child of the root.
    """

    def __init__(self, num_simulations=1000, playout_policy=None):
        super().__init__()
        self.num_simulations = num_simulations
        self.playout_policy = playout_policy
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
        """Expand the leaf node by generating one child per legal action. Return a random child."""
        from src.rl.mcts import Node

        if leaf.state.is_game_over():
            return leaf

        actions = self._get_legal_actions(leaf.state)
        if not actions:
            return leaf

        for action in actions:
            child_state = self._apply_action(leaf.state, action)
            child = Node(state=child_state, parent=leaf, action=action)
            leaf.children.append(child)

        return leaf.children[np.random.randint(len(leaf.children))]

    def _get_legal_actions(self, state):
        """Enumerate legal actions based on the current phase."""
        player = state.get_current_player()
        if state.phase == CHOOSE_ACTION:
            return player._enumerate_legal_actions(state.get_tray(), state.get_bird_deck())
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return player._enumerate_playable_birds()
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            choices = list(state.get_tray().see_birds_in_tray())
            if state.get_bird_deck().get_count() > 0:
                choices.append("deck")
            return choices
        else:
            raise ValueError(f"Unexpected phase: {state.phase}")

    def _apply_action(self, state, action):
        """Clone the state and apply a single action, returning the new state."""
        new_state = copy.deepcopy(state)
        player = new_state.get_current_player()

        if state.phase == CHOOSE_ACTION:
            if action == "gain_food":
                player.gain_food(new_state.get_bird_feeder())
                new_state.end_player_turn(player)
            elif action == "play_a_bird":
                new_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
            elif action == "draw_a_bird":
                new_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)
            else:
                raise ValueError(f"Unexpected action '{action}' for phase {state.phase}")
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            food_cost = player.bird_hand.get_card(action).get_food_cost()
            player.food_supply.decrement(food_cost)
            player.bird_hand.play_bird(action, player.game_board)
            new_state.end_player_turn(player)
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            if action == "deck":
                player.bird_hand.draw_card_from_deck(new_state.get_bird_deck())
            else:
                player.bird_hand.draw_bird_from_tray(new_state.get_tray(), action)
            new_state.end_player_turn(player)
        else:
            raise ValueError(f"Unexpected phase: {state.phase}")

        return new_state

    def _playout(self, node):
        """Simulate a game from this node to completion.

        Uses playout_policy if provided, otherwise defaults to RandomPolicy.
        """
        from src.entities.game_state import MCTSGameState

        # Clone state via determinization
        sim_state = MCTSGameState.from_representation(
            node.state.to_representation(), playout_policy=self.playout_policy
        )

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
        """Propagate reward up the tree, updating visits and rewards."""
        while node is not None:
            node.num_visits += 1
            node.total_reward += reward
            node = node.parent

    def _run_simulations(self, root, num_simulations):
        """Run the MCTS loop: select leaf, expand, playout, backpropagate."""
        for _ in range(num_simulations):
            leaf = self._select_leaf(root)
            unexplored_node = self._expand(leaf)
            reward = self._playout(unexplored_node)
            self._backpropagate(unexplored_node, reward)

    def _best_child(self, node):
        """Choose the child with the highest visit count."""
        return max(node.children, key=lambda child: child.num_visits)
