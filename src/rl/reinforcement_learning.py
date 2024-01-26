from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
from data.bird_list import birds as bird_list
from src.entities.game_state import GameState
from src.entities.deck import Deck
from src.entities.tray import Tray
from src.entities.hand import BirdHand
from src.entities.food_supply import FoodSupply
from src.entities.gameboard import GameBoard
from src.entities.player import BotPlayer
from src.entities.birdfeeder import BirdFeeder
from src.rl.mcts import Node
from typing import List, FrozenSet, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.player import Player

class State:
    def __init__(self, game_state: GameState, legal_actions: List[str]) -> None:
        self.game_state = game_state
        self.legal_actions = legal_actions

    def _represent_bird_deck(self) -> int:
        """Returns a representation of the bird deck, that appropriately represents hidden information."""
        #TODO: add a ledger of known missing cards
        return self.game_state.get_bird_deck().get_count()
    
    def _represent_discard_pile(self) -> int:
        """Returns a representation of the discard pile, that appropriately represents hidden information."""
        return self.game_state.get_discard_pile().get_count()
    
    def _represent_player(self, player: 'Player', full: bool=True) -> FrozenSet[tuple]:
        """
        Returns a representation of the player, that appropriately represents hidden information.
        
        Args:
            player (Player): The player to represent.
            full (bool): Whether to return a full representation of the player, or a partial representation with hidden information.
        """
        # public information for all players
        player_dict = {
            'food_supply': player.get_food_supply().to_representation(),
            'game_board': player.get_game_board().to_representation()
        }

        # private information to each player
        if full:
            # full representation
            player_dict['hand'] = player.get_bird_hand().to_representation()
        else:
            # representation with hidden information
            player_dict['hand'] = player.get_bird_hand().get_count()
            #TODO: add a ledger of known cards drawn from the tray that haven't yet been played

        return frozenset(player_dict.items())

    def _get_opponents(self, player: 'Player') -> List['Player']:
        """
        Returns a list of the opponents of the player, ordered by next player.
        
        Args:
            player (Player): The player whose opponents to return.
        """
        # get the players ordered by initial turn order
        players = self.game_state.get_players()
        
        # get the index of the player
        num_players = len(players)
        player_index = self.game_state.get_game_turn() % num_players

        # reorder players so that the next opponent is first, and the player is removed
        opponents = players[player_index+1:] + players[:player_index]
        
        return opponents
    
    def _reorder_players(self, current_player: 'Player', opponents: List['Player'], game_turn: int) -> List['Player']:
        """
        Returns a list of the players, ordered by the player who started the game.

        Args:
            current_player (Player): The current player.
            opponents (List[Player]): The opponents of the current player, ordered by next player
            game_turn (int): The current game turn.
        """
        # get the index of the player
        num_players = len(opponents) + 1
        player_turn_number = game_turn % num_players

        # reorder players so that the player who started the game is first
        players = [current_player] + opponents
        reordered_players = players[-player_turn_number:] + players[:-player_turn_number]
        
        return reordered_players
    
    def _get_turns_remaining(self, num_turns: int, game_turn: int, num_players: int) -> int:
        """
        Returns the number of turns remaining for the current player
        
        Args:
            num_turns (int): The total number of turns each player gets.
            game_turn (int): The current game turn, max = num_players * num_turns
            num_players (int): The number of players in the game.
        """
        return num_turns - (game_turn // num_players)
    
    def _construct_player(self, hand: BirdHand, representation: dict, deck: Deck, game_turn: int, num_turns: int, num_players: int, name: str) -> BotPlayer:
        """Constructs a player from a representation."""

        food_supply = FoodSupply(initial_amount=representation['food_supply'])
        game_board = GameBoard.from_representation(representation['game_board'], deck)
        num_turns_remaining = self._get_turns_remaining(num_turns=num_turns, game_turn=game_turn, num_players=num_players)
        return BotPlayer(
            name=name,
            hand=hand,
            food_supply=food_supply,
            game_board=game_board,
            num_turns=num_turns_remaining
        )

    def to_representation(self) -> FrozenSet[tuple]:
        """Returns a representation of the game state."""
        state_dict = {
            'num_turns': self.game_state.get_num_turns(),
            'game_turn': self.game_state.get_game_turn(),
            'phase': self.game_state.get_phase(),
            'bird_deck': self._represent_bird_deck(),
            'discard_pile': self._represent_discard_pile(),
            'tray': self.game_state.tray.to_representation(),
            'bird_feeder': self.game_state.bird_feeder.to_representation(),
            'current_player': self._represent_player(self.game_state.get_current_player(), full=True),
            'opponents': (self._represent_player(player, full=False) for player in self.get_opponents(self.game_state.get_current_player()))
        }
        return frozenset(state_dict.items())
    
    def from_representation(self, representation: FrozenSet[tuple]) -> GameState:
        """Reconstructs the game state from a representation."""
        state_dict = dict(representation)

        # Start with a valid starting deck
        valid_bird_deck = Deck()
        valid_bird_deck.prepare_deck(bird_list)
        
        # construct the tray
        tray = Tray.from_representation(state_dict['tray'], valid_bird_deck)

        # construct the current player
        representation_current_player = dict(state_dict['current_player'])
        hand_current_player = BirdHand.from_representation(representation_current_player['hand'], valid_bird_deck)
        num_opponents = len(state_dict['opponents'])
        current_player = self._construct_player(
            hand=hand_current_player,
            representation=representation_current_player,
            deck=valid_bird_deck,
            game_turn=state_dict['game_turn'],
            num_turns=state_dict['num_turns'],
            num_players=num_opponents + 1,
            name="current_player"
        )

        # construct the opponents
        opponents = []
        opponent_game_turn = state_dict['game_turn']
        for i in range(num_opponents):
            representation_opponent = dict(state_dict['opponents'][i])
            hand_opponent = BirdHand()
            for _ in range(representation_opponent['hand']):
                bird = valid_bird_deck.draw_card()
                hand_opponent.add_card(bird, bird.get_name())
            opponent_game_turn += 1 #increment the game turn, since opponents are ordered by next opponent
            opponents.append(self._construct_player(
                hand=hand_opponent,
                representation=representation_opponent,
                deck=valid_bird_deck,
                game_turn=opponent_game_turn,
                num_turns=state_dict['num_turns'],
                num_players=num_opponents + 1,
                name=f"opponent_{i}"
            ))

        # reorder the players, so that the player who started the game is in the 0th position
        players = self._reorder_players(current_player=current_player, opponents=opponents, game_turn=state_dict['game_turn'])
        
        ## discard the correct number of cards from the deck and validate
        valid_discard_pile = Deck()
        cards_to_discard = state_dict['discard_pile']
        if cards_to_discard != valid_bird_deck.get_count() - state_dict['bird_deck']:
            raise ValueError(f"Number of cards to discard: {cards_to_discard} does not match the representation of the discard pile: {state_dict['discard_pile']}")
        for _ in range(cards_to_discard):
            valid_discard_pile.add_card(valid_bird_deck.draw_card())

        # reconstruct the bird feeder
        bird_feeder = BirdFeeder(food_count=state_dict['bird_feeder'])
        
        return GameState(
            num_turns=state_dict['num_turns'],
            game_turn=state_dict['game_turn'],
            phase=state_dict['phase'],
            bird_deck=valid_bird_deck,
            discard_pile=valid_discard_pile,
            tray=tray,
            bird_feeder=bird_feeder,
            players=players
        )

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