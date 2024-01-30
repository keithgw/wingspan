from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
import numpy as np
from src.rl.mcts import Node
from src.entities.game_state import MCTSGameState
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
    def _uniform_random_choice(self, actions: List[str]) -> str:
        """
        Return a choice uniformly at random from the list of actions.
        
        Args:
            actions (List[str]): The list of choices.
            
        Returns:
            str: The chosen action.
        """
        # by default, random.choice chooses uniformly at random
        return np.random.choice(actions)
    
    def _policy_choose_action(self, state: 'GameState', legal_actions: List[str]) -> str:
        """
        Return a legal action uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            legal_actions (List[str]): The list of legal actions.

        Returns:
            str: The action to take.
        """
        return self._uniform_random_choice(legal_actions)

    def _policy_choose_a_bird_to_play(self, state: 'GameState', playable_birds: List[str]) -> str:
        """
        Return a playable bird name uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            playable_birds (List[str]): The list of playable birds.
            
        Returns:
            str: The bird name to play.
        """
        return self._uniform_random_choice(playable_birds)

    def _policy_choose_a_bird_to_draw(self, state: 'GameState', valid_choices: List[str]) -> str:
        """
        Return a bird from the tray or 'deck' uniformly at random
        
        Args:
            state (GameState): The current state of the game. Not used in this policy.
            valid_choices (List[str]): Bird names from the tray and/or 'deck' if there are cards in the deck.
            
        Returns:
            str: The bird name to draw from the tray or 'deck' to draw from the deck.
        """
        return self._uniform_random_choice(valid_choices)
        
class MCTSPolicy(Policy):
    def __init__(self, num_simulations=1000, *args, **kwargs):
        super().__init__()
        self.num_simulations = num_simulations
        self.root = None

    def _rhoUCT(self, state: 'GameState', actions: List[str]) -> str:
        """
        Upper Confidence Bounds for Trees (UCT) algorithm for MCTS with an environment model, rho.
        Return an action from actions according to max_a[Q(s, a)]

        Args:
            state (GameState): The current state of the game.
            actions (List[str]): The list of legal actions.

        Returns:
            best_action (str): The action that maximizes the estimated action-value function Q:(s, a) -> R.
        """
        # Initialize root node with current state
        state = MCTSGameState.from_game_state(state)
        candidate_root = Node(state=state, node_type='decision')
        
        # check if the root node is a decision node in the tree
        # if not, initialize the root node with current state
        if self.root is None:
            # No subtree exists to use as the root
            root = candidate_root
        elif self.root.is_decision_node():
            # check if the current state matches a decision node in the tree
            if self.root == candidate_root:
                root = self.root
            else:
                # the current state has not been explored in a previous simulation
                root = candidate_root
        elif self.root.is_chance_node():
            # use BFS to find the decison nodes closest to the root
            children = self.root.get_children()
            queue = list(children)
            root = None # Initialize root to None in case BFS doesn't find a matching node
            while queue:
                node = queue.pop(0)
                if node.is_decision_node():
                    # do not add children of decision nodes to the queue
                    if node == candidate_root:
                        root = node
                        break
                elif node.is_chance_node():
                    queue.extend(node.get_children())
            if root is None:
                # BFS did not return any matching decision nodes to the candidate root
                root = candidate_root

        assert root.is_decision_node(), f"The root node is not a decision node: {root.node_type}"
            
        # Estimate the value of each action by running simulations from the root
        #TODO: simulation should subtract from num simulations the number of visits to the root node in previous simluations
        #TODO: can simulation be more efficient by only exploring legal actions?
        self._run_simulations(root, self.num_simulations) 

        # Choose the action that leads to the child with the highest expected value
        best_child = self._best_child(root)
        best_action = best_child.get_action()

        # persist the subtree rooted at the best child
        self.root = best_child

        # Ensure the chosen action is among the legal actions
        assert best_action in actions, f"Chosen action must be one of {actions}, but was {best_action}."

        return best_action

    def _policy_choose_action(self, state: 'GameState', legal_actions: List[str]) -> str:
        """Return one of 'play_a_bird', 'gain_food', 'draw_a_card' according to max_a Q(s, a)"""
        return self._rhoUCT(state=state, actions=legal_actions)
        
    def _policy_choose_a_bird_to_play(self, state: 'GameState', playable_birds: List[str]) -> str:
        """Return a bird name from the hand according to max_a Q(s, a)"""
        return self._rhoUCT(state=state, actions=playable_birds)

    def _policy_choose_a_bird_to_draw(self, state: 'GameState', valid_choices: List[str]) -> str:
        """Return a bird name from the tray or 'deck' according to max_a Q(s, a)"""
        return self._rhoUCT(state=state, actions=valid_choices)
    
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