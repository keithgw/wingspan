from src.entities.deck import Deck
from src.entities.tray import Tray
from src.entities.birdfeeder import BirdFeeder
from typing import List
from src.entities.hand import BirdHand
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.player import Player

class GameState:
    VALID_PHASES = ['choose_action', 'choose_a_bird_to_play', 'choose_a_bird_to_draw']
    def __init__(self, num_turns: int, bird_deck: Deck, discard_pile: Deck, tray: Tray, bird_feeder: BirdFeeder, players: List['Player']):
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
        self.num_turns = num_turns
        self.num_players = len(players)
        self.game_turn = 0 # increments by 1 each player turn, so will end at num_players * num_turns
        self.phase = self.VALID_PHASES[0] # phases are intra-turn, so reset to 0 at the start of each player turn
        self.bird_deck = bird_deck
        self.discard_pile = discard_pile
        self.tray = tray
        self.bird_feeder = bird_feeder
        self.players = players

    def get_num_turns(self) -> int:
        '''Returns the total number of turns in the game.'''
        return self.num_turns
    
    def get_bird_deck(self) -> Deck:
        '''Returns the bird deck.'''
        return self.bird_deck
    
    def get_discard_pile(self) -> Deck:
        '''Returns the discard pile.'''
        return self.discard_pile
    
    def get_tray(self) -> Tray:
        '''Returns the bird tray.'''
        return self.tray
    
    def get_bird_feeder(self) -> BirdFeeder:
        '''Returns the bird feeder.'''
        return self.bird_feeder
    
    def get_players(self) -> List['Player']:        
        '''Returns the list of players.'''
        return self.players
    
    def get_player(self, idx: int) -> 'Player':
        '''Returns the player at the given index. Players are indexed by initial turn order.'''
        return self.players[idx]

    def get_current_player(self) -> 'Player':
        '''Returns the current player'''
        player_idx = self.game_turn % self.num_players
        return self.players[player_idx]

    def end_player_turn(self, player: 'Player'):
        '''
        Ends the given player's turn.

        Args:
            player (Player): The player whose turn is ending.
        '''
        # check if the tray needs to be refilled
        if self.tray.is_not_full():
            self.tray.refill(self.bird_deck)
            #TODO: update known_missing_cards for each BotPlayer
        
        # manage turn accounting
        player.end_turn()
        self.game_turn += 1
        self.phase = self.VALID_PHASES[0]

    def is_game_over(self) -> bool:
        '''Returns True if the game is over, False otherwise.'''
        return self.game_turn == self.num_turns * self.num_players