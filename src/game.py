from src.entities.game_state import GameState
from src.entities.gameboard import Gameboard
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.entities.food_supply import FoodSupply

class WingspanGame:
    def __init__(self, num_players=1, num_turns=10):
        '''Initializes the game.'''
        # Initizialize the game state
        self.game_state = GameState(num_players, num_turns)

        # Initialize the game board
        self.game_board = Gameboard()

        # Initialize the bird feeder
        self.bird_feeder = BirdFeeder()
        self.bird_feeder.reroll()

        # Initialize the bird deck
        self.bird_deck = Deck()
        for bird in bird_list:
            self.bird_deck.add_card(bird)

        # Initialize the discard pile
        self.discard_pile = Deck()

        # Initialize the player hands


        # Initialize the bird tray

        # Initialize the player food supplies

    def setup(self):
        # Set up the game board and any initial game state
        pass

    def play(self):
        # Main game loop
        while not self.is_game_over():
            self.take_turn()
            self.update_game_state()
            self.render()

    def take_turn(self):
        # Logic for a single player's turn
        pass

    def update_game_state(self):
        # Update the game state after each turn
        pass

    def render(self):
        # Render the current game state
        pass

    def is_game_over(self):
        # Check if the game is over
        pass

if __name__ == "__main__":
    game = WingspanGame()
    game.setup()
    game.play()
