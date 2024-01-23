from src.rl.mcts import Node

class State:
    VALID_PHASES = ['choose_action', 'choose_a_bird_to_play', 'choose_a_bird_to_draw']
    def __init__(self, game_board, bird_hand, food_supply, phase, tray, bird_deck, legal_actions):
        if phase not in self.VALID_PHASES:
            raise ValueError(f"Invalid phase {phase}, must be one of {self.VALID_PHASES}")
        self.game_board = game_board
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.phase = phase
        self.tray = tray
        self.bird_deck = bird_deck
        self.legal_actions = legal_actions

class Policy:
    def __call__(self, state):
        if state.phase == 'choose_action':
            return self._policy_choose_action(state.legal_actions)
        elif state.phase == 'choose_a_bird_to_play':
            return self._policy_choose_a_bird_to_play(state.bird_hand, state.food_supply)
        else:
            return self._policy_choose_a_bird_to_draw(state.tray, state.bird_deck)

    def _policy_choose_action(self, legal_actions):
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, tray, deck):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        raise NotImplementedError

class RandomPolicy(Policy):
    def _policy_choose_action(self, legal_actions):
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'

        # uniform random policy
        probabilities = [1/len(legal_actions)] * len(legal_actions)
        return probabilities

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        
        birds = hand.get_cards_in_hand()
        is_playable = [food_supply.can_play_bird(bird) for bird in birds]
        
        # set probability=0 for birds that cannot be played, else uniform random policy
        uniform_prob = 1/sum(is_playable)
        probabilities = [uniform_prob if playable else 0 for playable in is_playable]

        return probabilities

    def _policy_choose_a_bird_to_draw(self, tray, deck):
        # Return probabilities for the actions 'choose_bird_i' for i in tray, 'choose_from_deck'
        
        # uniform random policy
        num_birds_in_tray = tray.get_count()

        # deck is empty:
        if deck.get_count() == 0:
            return [1/num_birds_in_tray] * num_birds_in_tray + [0]
        else:
            return [1/(num_birds_in_tray + 1)] * (num_birds_in_tray + 1)
        
class MCTSPolicy(Policy):
    def __init__(self, num_simulations=1000, *args, **kwargs):
        super().__init__()
        self.num_simulations = num_simulations

    def _policy_choose_action(self, legal_actions):
        # Initialize root node with current state
        root = Node(state=self.state)

        # Run simulations
        self._run_simulations(root, self.num_simulations)

        # Choose the action of the child of root with the highest average reward
        best_action = self._best_child(root).action

        return best_action

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, tray, deck):
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