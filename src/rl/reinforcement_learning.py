from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
from src.entities.game_state import GameState
from src.rl.mcts import Node
from typing import List, FrozenSet, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.player import Player

class State:
    def __init__(self, game_state: GameState, legal_actions: List[str]) -> None:
        self.game_state = game_state
        self.legal_actions = legal_actions

    def represent_bird_deck(self) -> int:
        """Returns a representation of the bird deck, that appropriately represents hidden information."""
        return self.game_state.get_bird_deck().get_count()
    
    def represent_discard_pile(self) -> int:
        """Returns a representation of the discard pile, that appropriately represents hidden information."""
        return self.game_state.get_discard_pile().get_count()
    
    def represent_player(self, player: 'Player') -> FrozenSet[tuple]:
        """Returns a representation of the player, that appropriately represents hidden information."""
        #TODO: implement full and partial representations of player
        # turns remaining unecessary, as game turn, current player, and ordering the opponents by next_player=0 is sufficient
        pass 

    def get_opponents(self, player: 'Player') -> List['Player']:
        """Returns a list of the opponents of the player, ordered by next player."""
        #TODO: implement get_opponents
        pass
        
    def to_representation(self) -> FrozenSet[tuple]:
        """Returns a representation of the game state."""
        state_dict = {
            'num_turns': self.game_state.get_num_turns(),
            'game_turn': self.game_state.get_game_turn(),
            'phase': self.game_state.get_phase(),
            'bird_deck': self.represent_bird_deck(),
            'discard_pile': self.represent_discard_pile(),
            'tray': self.game_state.tray.to_representation(),
            'bird_feeder': self.game_state.bird_feeder.to_representation(),
            'current_player': self.game_state.get_current_player().to_representation_full(), #TODO: implement full and partial representations of player
            'opponents': (self.represent_player(player) for player in self.get_opponents(self.game_state.get_current_player())), #TODO: implement get_opponents
        }
        return frozenset(state_dict.items())
    
    def from_representation(representation) -> GameState:
        """Reconstructs the game state from a representation."""
        state_dict = dict(representation)
        bird_deck = BirdDeck.from_representation(state_dict['bird_deck'])
        discard_pile = DiscardPile.from_representation(state_dict['discard_pile'])
        tray = Tray.from_representation(state_dict['tray'])
        bird_feeder = BirdFeeder.from_representation(state_dict['bird_feeder'])
        players = [Player.from_representation(player_repr) for player_repr in state_dict['players']]
        return GameState(state_dict['num_turns'], state_dict['num_players'], state_dict['game_turn'], state_dict['phase'], bird_deck, discard_pile, tray, bird_feeder, players)

class Policy:
    def __call__(self, state):
        if state.phase == CHOOSE_ACTION:
            return self._policy_choose_action(state.legal_actions)
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return self._policy_choose_a_bird_to_play(state.game_state.get_bird_hand(), state.game_state.get_food_supply())
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            return self._policy_choose_a_bird_to_draw(state.game_state.get_tray(), state.game_state.get_bird_deck()) #TODO: this shouldn't need the deck, just a count

    def _policy_choose_action(self, legal_actions): #TODO: this shouldn't need legal_actions, they should be handled by querying the game_state
        # Return probabilities for the actions 'play_a_bird', 'gain_food', 'draw_a_card'
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, hand, food_supply):
        # Return probabilities for the actions 'play_bird_i' for i in hand
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, tray, deck): #TODO: this shouldn't need the deck, just a count of cards in the deck, or bool deck.get_count() > 0
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