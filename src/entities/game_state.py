from src.constants import VALID_PHASES
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.food_supply import FoodSupply
from src.entities.gameboard import GameBoard
from src.entities.tray import Tray
from src.entities.deck import Deck
from src.entities.birdfeeder import BirdFeeder
from typing import List, FrozenSet, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.player import Player, BotPlayer

class GameState:
    def __init__(self, num_turns: int, bird_deck: Deck, discard_pile: Deck, tray: Tray, bird_feeder: BirdFeeder, players: List['Player'], game_turn: int=0, phase: str=VALID_PHASES[0]):
        """
        Initialize a new game state with the minimum required elements to create a valid game state.

        Args:
            num_turns (int): The total number of turns in the game.
            bird_deck (Deck): The bird deck from which players can draw cards.
            discard_pile (Deck): The discard pile, which is initially empty.
            tray (Tray): The bird tray, containing 3 face-up birds which the player can draw.
            bird_feeder (BirdFeeder): The bird feeder, containing 5 dice which the player can reroll when empty.
            players (List[Player]): The list of players in the game, indexed by initial turn order. Each player maintains their own hand, game board, and food supply.
        """
        # Validate inputs and assign to attributes
        if num_turns < 0:
            raise ValueError("num_turns must be non-negative.")
        self.num_turns = num_turns
        self.num_players = len(players)

        if game_turn > num_turns * self.num_players: # increments by 1 each player turn, so will end at num_players * num_turns
            raise ValueError("game_turn must be less than or equal to num_turns * num_players.")
        self.game_turn = game_turn 
        if phase not in VALID_PHASES:
            raise ValueError(f"phase must be one of {VALID_PHASES}.")
        self.phase = phase
        self.bird_deck = bird_deck
        self.discard_pile = discard_pile
        self.tray = tray
        self.bird_feeder = bird_feeder
        self.players = players

    def get_num_turns(self) -> int:
        """Returns the total number of turns in the game."""
        return self.num_turns
    
    def get_game_turn(self) -> int:
        """Returns the current game turn."""
        return self.game_turn
    
    def get_phase(self) -> str:
        """Returns the current phase."""
        return self.phase
    
    def set_phase(self, phase: str) -> None:
        """Sets the current phase."""
        if phase not in VALID_PHASES:
            raise ValueError(f"phase must be one of {VALID_PHASES}, received {phase}.")
        self.phase = phase
    
    def get_bird_deck(self) -> Deck:
        """Returns the bird deck."""
        return self.bird_deck
    
    def get_discard_pile(self) -> Deck:
        """Returns the discard pile."""
        return self.discard_pile
    
    def get_tray(self) -> Tray:
        """Returns the bird tray."""
        return self.tray
    
    def get_bird_feeder(self) -> BirdFeeder:
        """Returns the bird feeder."""
        return self.bird_feeder
    
    def get_players(self) -> List['Player']:        
        """Returns the list of players."""
        return self.players
    
    def get_player(self, idx: int) -> 'Player':
        """
        Returns the player at the given index. Players are indexed by initial turn order.
        
        Args:
            idx (int): The index of the player to return.
        """
        return self.players[idx]

    def get_current_player(self) -> 'Player':
        """Returns the current player"""
        player_idx = self.game_turn % self.num_players
        return self.players[player_idx]

    def end_player_turn(self, player: 'Player'):
        """
        Ends the given player's turn.

        Args:
            player (Player): The player whose turn is ending.
        """
        # check if the tray needs to be refilled
        if self.tray.is_not_full():
            self.tray.refill(self.bird_deck)
            #TODO: update known_missing_cards for each BotPlayer
        
        # manage turn accounting
        player.end_turn()
        self.game_turn += 1
        self.phase = VALID_PHASES[0]

    def is_game_over(self) -> bool:
        """Returns True if the game is over, False otherwise."""
        return self.game_turn == self.num_turns * self.num_players
    
class MCTSGameState(GameState):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def set_tray(self, tray: Tray) -> None:
        """Sets the tray to the given tray."""
        self.tray = tray

    def set_players(self, players: List['Player']) -> None:
        """Sets the players to the given list of players."""
        self.players = players

    def _represent_bird_deck(self) -> int:
        """Returns a representation of the bird deck, that appropriately represents hidden information."""
        #TODO: add a ledger of known missing cards
        return self.bird_deck.get_count()
    
    def _represent_discard_pile(self) -> int:
        """Returns a representation of the discard pile, that appropriately represents hidden information."""
        return self.discard_pile.get_count()
    
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

    def _get_opponents(self) -> List['Player']:
        """Returns a list of the opponents of the current player, ordered by next player."""
        # get the index of the player
        player_index = self.game_turn % self.num_players

        # reorder players so that the next opponent is first, and the current player is removed
        opponents = self.players[player_index+1:] + self.players[:player_index]
        
        return opponents
    
    def _reorder_players(self, current_player: 'Player', opponents: List['Player'], game_turn: int) -> List['Player']:
        """
        Returns a list of the players, ordered by the player who started the game.
        Used for reconstructing a GameState from a representation.

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
        Returns the number of turns remaining for a player at the given game turn.
        Used for reconstructing a GameState from a representation.
        
        Args:
            num_turns (int): The total number of turns each player gets.
            game_turn (int): The current game turn, max = num_players * num_turns
            num_players (int): The number of players in the game.
        """
        return num_turns - (game_turn // num_players)
    
    def _construct_player(self, hand: BirdHand, representation: dict, deck: Deck, game_turn: int, num_turns: int, num_players: int, name: str) -> 'BotPlayer':
        """Constructs a player from a representation."""
        # import here to avoid circular imports
        from src.utilities.player_factory import create_bot_player

        food_supply = FoodSupply(initial_amount=representation['food_supply'])
        game_board = GameBoard.from_representation(representation['game_board'], deck)
        num_turns_remaining = self._get_turns_remaining(num_turns=num_turns, game_turn=game_turn, num_players=num_players)
        bot_player = create_bot_player(
            name=name,
            bird_hand=hand,
            food_supply=food_supply,
            game_board=game_board,
            num_turns=num_turns_remaining
        )
        return bot_player

    def to_representation(self) -> FrozenSet[tuple]:
        """Returns a representation of the game state."""
        state_dict = {
            'num_turns': self.num_turns,
            'game_turn': self.game_turn,
            'phase': self.phase,
            'bird_deck': self._represent_bird_deck(),
            'discard_pile': self._represent_discard_pile(),
            'tray': self.tray.to_representation(),
            'bird_feeder': self.bird_feeder.to_representation(),
            'current_player': self._represent_player(self.get_current_player(), full=True),
            'opponents': tuple(self._represent_player(player, full=False) for player in self._get_opponents())
        }
        return frozenset(state_dict.items())
    
    @classmethod
    def from_representation(cls, representation: FrozenSet[tuple]) -> 'MCTSGameState':
        """Reconstructs the game state from a representation."""
        state_dict = dict(representation)

        # reconstruct the bird feeder
        bird_feeder = BirdFeeder(food_count=state_dict['bird_feeder'])
        
        # intialize the game state with None as placeholders
        num_opponents = len(state_dict['opponents'])
        game_state =  cls(
            num_turns=state_dict['num_turns'],
            game_turn=state_dict['game_turn'],
            phase=state_dict['phase'],
            bird_feeder=bird_feeder,
            bird_deck=Deck(),
            discard_pile=Deck(),
            tray=None,
            players=[None] * (num_opponents + 1)
        )

        # Start with a valid starting deck
        valid_bird_deck = game_state.get_bird_deck()
        valid_bird_deck.prepare_deck(bird_list)
        
        # construct the tray
        game_state.set_tray(Tray.from_representation(state_dict['tray'], valid_bird_deck))

        # construct the current player
        representation_current_player = dict(state_dict['current_player'])
        hand_current_player = BirdHand.from_representation(representation_current_player['hand'], valid_bird_deck)
        current_player = game_state._construct_player(
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
            opponents.append(game_state._construct_player(
                hand=hand_opponent,
                representation=representation_opponent,
                deck=valid_bird_deck,
                game_turn=opponent_game_turn,
                num_turns=state_dict['num_turns'],
                num_players=num_opponents + 1,
                name=f"opponent_{i}"
            ))

        # reorder the players, so that the player who started the game is in the 0th position
        game_state.set_players(game_state._reorder_players(current_player=current_player, opponents=opponents, game_turn=state_dict['game_turn']))
        
        ## discard the correct number of cards from the deck and validate
        valid_discard_pile = game_state.get_discard_pile()
        cards_to_discard =  valid_bird_deck.get_count() - state_dict['bird_deck']
        if cards_to_discard != state_dict['discard_pile']:
            raise ValueError(f"Number of cards to discard: {cards_to_discard} does not match the representation of the discard pile: {state_dict['discard_pile']}")
        for _ in range(cards_to_discard):
            valid_discard_pile.add_card(valid_bird_deck.draw_card())
        
        return game_state
    
    @classmethod
    def from_game_state(cls, game_state: GameState) -> 'MCTSGameState':
        """Create a new MCTSGameState object with the values from the GameState object"""
        return cls(
            num_turns=game_state.num_turns,
            bird_deck=game_state.bird_deck,
            discard_pile=game_state.discard_pile,
            tray=game_state.tray,
            bird_feeder=game_state.bird_feeder,
            players=game_state.players,
            game_turn=game_state.game_turn,
            phase=game_state.phase
        )