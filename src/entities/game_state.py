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
        self.player_turns = [0] * num_players # keeps track of how many turns each player has taken
        self.player_names = [f'Player {i + 1}' for i in range(num_players)]

    def get_num_turns(self):
        '''Returns the total number of turns in the game.'''
        return self.num_turns

    def get_current_player(self):
        '''Returns the current player'''
        return self.game_turn % self.num_players
    
    def get_player_name(self, player):
        '''Returns the name of the given player'''
        return self.player_names[player]

    def set_player_name(self, player, name):
        '''Sets the name of the given player'''
        self.player_names[player] = name

    def end_player_turn(self):
        '''
        Increments the current turn and the current player's turn count.
        Players' turns will increment by one each time it is their turn.
        Game turn will increment by one each time a player's turn ends.
        '''
        self.player_turns[self.get_current_player()] += 1
        self.game_turn += 1

    def get_turns_remaining(self):
        '''Returns the number of turns remaining in the game as a list indexed by player.'''
        return [self.num_turns - turn for turn in self.player_turns]
