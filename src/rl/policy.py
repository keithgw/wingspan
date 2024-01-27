from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
import numpy as np
from src.rl.mcts import Node
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.game_state import GameState

class Policy:
    def __call__(self, state: 'GameState'):
        if state.phase == CHOOSE_ACTION:
            return self._policy_choose_action(state)
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return self._policy_choose_a_bird_to_play(state)
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            return self._policy_choose_a_bird_to_draw(state)

    def _policy_choose_action(self):
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, state: 'GameState'):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, state: 'GameState'):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        raise NotImplementedError

class RandomPolicy(Policy):
    def _policy_choose_action(self) -> str:
        # Return a legal action uniformly at random

        # get legal actions
        legal_actions = self.state.get_current_player().enumerate_legal_actions()

        # uniform random policy
        n_actions = len(legal_actions)
        probabilities = [1/n_actions] * n_actions
        return np.random.choice(legal_actions, p=probabilities)

    def _policy_choose_a_bird_to_play(self, state: 'GameState') -> str:
        # Return probabilities for the actions 'play_bird_i' for i in hand

        current_player = state.get_current_player()
        hand = current_player.get_bird_hand()
        food_supply = current_player.get_food_supply()
        
        birds = hand.get_cards_in_hand()
        is_playable = [food_supply.can_play_bird(bird) for bird in birds]
        
        # set probability=0 for birds that cannot be played, else uniform random policy
        uniform_prob = 1/sum(is_playable)
        probabilities = [uniform_prob if playable else 0 for playable in is_playable]

        # Choose an action according to the probabilities
        chosen_bird = np.random.choice(birds, p=probabilities)

        # Convert the action back to a bird name
        return chosen_bird.get_name()

    def _policy_choose_a_bird_to_draw(self, state: 'GameState'):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'

        tray = state.get_tray()
        
        # uniform random policy
        num_birds_in_tray = tray.get_count()

        # deck is empty:
        if state.get_bird_deck().get_count() == 0:
            return [1/num_birds_in_tray] * num_birds_in_tray + [0]
        else:
            return [1/(num_birds_in_tray + 1)] * (num_birds_in_tray + 1)
        
class MCTSPolicy(Policy):
    def __init__(self, num_simulations=1000, *args, **kwargs):
        super().__init__()
        self.num_simulations = num_simulations

    def _policy_choose_action(self, state: 'GameState'):
        # Initialize root node with current state
        root = Node(state=self.state)

        # Run simulations
        self._run_simulations(root, self.num_simulations)

        # Choose the action of the child of root with the highest average reward
        best_action = self._best_child(root).action

        return best_action

    def _policy_choose_a_bird_to_play(self, state: 'GameState'):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, state: 'GameState'):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        raise NotImplementedError
    
    def _select_child(self, node: Node) -> Node:
        # The tree policy, used to traverse the explored tree to find an unexplored or terminal node
        # Select a child node using UCB
        return max(node.children, key=self._ucb)
    
    def _select_leaf(self, root: Node) -> Node:
        # Traverse the tree until we reach a leaf node
        node = root
        while not node.is_leaf():
            node = self._select_child(node)
        return node

    def _expand(self, leaf: Node) -> Node:
        # Expand the leaf node
        return leaf.expand()
    
    def _playout(self, node: Node) -> None:
        # Simulate a game from the node
        raise NotImplementedError
    
    def _backpropagate(self, node: Node, reward: float) -> None:
        # Backpropagate the reward up the tree
        raise NotImplementedError
    
    def _run_simulations(self, root, num_simulations):
        for _ in range(num_simulations):
            # Selection: Start from the root and select a leaf node
            leaf = self._select_leaf(root)

            # Expansion: Add children to the leaf node, and choose one at random
            unexplored_node = self._expand(leaf)

            # Simulation: Run a simulation from the new node using RandomPolicy
            reward = self._playout(unexplored_node)

            # Backpropagation: Update the node statistics from the simulation
            self._backpropagate(unexplored_node, reward)
    
    def _best_child(self, node):
        # Choose the child of the node with the highest visit count
        return max(node.children, key=lambda child: child.visit_count)