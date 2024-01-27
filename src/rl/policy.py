from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
import numpy as np
# from src.rl.mcts import Node
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.game_state import GameState

class Policy:
    def __call__(self, state: 'GameState', actions: List[str]) -> str:
        if state.phase == CHOOSE_ACTION:
            return self._policy_choose_action(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return self._policy_choose_a_bird_to_play(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            return self._policy_choose_a_bird_to_draw(state, actions)

    def _policy_choose_action(self, state: 'GameState', legal_actions: List[str]) -> str:
        # Return one of 'play_a_bird', 'gain_food', 'draw_a_card' according to the probabilities
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, state: 'GameState', playable_birds: List[str]) -> str:
        # Return a bird name from the hand according to the probabilities
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, state: 'GameState', valid_choices: List[str]) -> str:
        # Return a bird name from the tray or 'deck' according to the probabilities
        raise NotImplementedError

class RandomPolicy(Policy):
    def _policy_choose_action(self, state: 'GameState', legal_actions: List[str]) -> str:
        """
        Return a legal action uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            legal_actions (List[str]): The list of legal actions.

        Returns:
            str: The action to take.
        """
        n_actions = len(legal_actions)
        probabilities = [1/n_actions] * n_actions
        return np.random.choice(legal_actions, p=probabilities)

    def _policy_choose_a_bird_to_play(self, state: 'GameState', playable_birds: List[str]) -> str:
        """
        Return a playable bird name uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            playable_birds (List[str]): The list of playable birds.
            
        Returns:
            str: The bird name to play.
        """
        n_birds = len(playable_birds)
        probabilities = [1/n_birds] * n_birds
        return np.random.choice(playable_birds, p=probabilities)

    def _policy_choose_a_bird_to_draw(self, state: 'GameState', valid_choices: List[str]) -> str:
        """
        Return a bird from the tray or 'deck' uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            valid_choices (List[str]): Bird names from the tray and/or 'deck' if there are cards in the deck.
            
        Returns:
            str: The bird name to draw from the tray or 'deck' to draw from the deck.
        """
        # Return a bird from the tray or 'deck' uniformly at random
        n_choices = len(valid_choices)
        probabilities = [1/n_choices] * n_choices
        return np.random.choice(valid_choices, p=probabilities)
        
# WIP
# class MCTSPolicy(Policy):
#     def __init__(self, num_simulations=1000, *args, **kwargs):
#         super().__init__()
#         self.num_simulations = num_simulations

#     def _policy_choose_action(self, state: 'GameState', legal_actions: List[str]) -> str:
#         # Initialize root node with current state
#         root = Node(state=self.state)

#         # Run simulations
#         self._run_simulations(root, self.num_simulations)

#         # Choose the action of the child of root with the highest average reward
#         best_action = self._best_child(root).action

#         return best_action

#     def _policy_choose_a_bird_to_play(self, state: 'GameState', playable_birds: List[str]) -> str:
#         # Return probabilities for the actions 'play_bird_i' for i in hand
#         raise NotImplementedError

#     def _policy_choose_a_bird_to_draw(self, state: 'GameState'):
#         # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
#         raise NotImplementedError
    
#     def _select_child(self, node: Node) -> Node:
#         # The tree policy, used to traverse the explored tree to find an unexplored or terminal node
#         # Select a child node using UCB
#         return max(node.children, key=self._ucb)
    
#     def _select_leaf(self, root: Node) -> Node:
#         # Traverse the tree until we reach a leaf node
#         node = root
#         while not node.is_leaf():
#             node = self._select_child(node)
#         return node

#     def _expand(self, leaf: Node) -> Node:
#         # Expand the leaf node
#         return leaf.expand()
    
#     def _playout(self, node: Node) -> None:
#         # Simulate a game from the node
#         raise NotImplementedError
    
#     def _backpropagate(self, node: Node, reward: float) -> None:
#         # Backpropagate the reward up the tree
#         raise NotImplementedError
    
#     def _run_simulations(self, root, num_simulations):
#         for _ in range(num_simulations):
#             # Selection: Start from the root and select a leaf node
#             leaf = self._select_leaf(root)

#             # Expansion: Add children to the leaf node, and choose one at random
#             unexplored_node = self._expand(leaf)

#             # Simulation: Run a simulation from the new node using RandomPolicy
#             reward = self._playout(unexplored_node)

#             # Backpropagation: Update the node statistics from the simulation
#             self._backpropagate(unexplored_node, reward)
    
#     def _best_child(self, node):
#         # Choose the child of the node with the highest visit count
#         return max(node.children, key=lambda child: child.visit_count)