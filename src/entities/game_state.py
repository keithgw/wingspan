from src.entities.hand import BirdHand

class GameState:
    def __init__(self, num_turns, num_players):
        """
        Initialize a new game state.

        Args:
            num_turns (int): The total number of turns in the game.
            num_players (int): The total number of players in the game.

        """
        self.num_turns = num_turns
        self.num_players = num_players
        self.game_turn = 0 # increments by 1 each player turn, so will end at num_players * num_turns

    def get_num_turns(self):
        '''Returns the total number of turns in the game.'''
        return self.num_turns

    def get_current_player(self):
        '''Returns the current player'''
        return self.game_turn % self.num_players

    def end_player_turn(self, player):
        '''
        Ends the given player's turn.

        Args:
            player (Player): The player whose turn is ending.
        '''
        player.end_turn()
        self.game_turn += 1

    def is_game_over(self):
        '''Returns True if the game is over, False otherwise.'''
        return self.game_turn == self.num_turns * self.num_players