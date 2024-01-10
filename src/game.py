from src.entities.game_state import GameState
from src.entities.gameboard import GameBoard
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.entities.food_supply import FoodSupply

# Constants
TOTAL_ALLOWED_IN_STARTING_HAND = 5
NUM_PLAYERS = 1 #TODO: get thse from STDIN
NUM_TURNS = 10

class WingspanGame:
    def __init__(self):
        self.game_board = GameBoard()
        self.discard_pile = Deck()

    def setup(self, num_players, num_turns, num_starting_cards=2):
        # Initizialize the game state, this handles turns and assigns empty player hands
        self.game_state = GameState(num_players, num_turns)

        # Initialize the bird feeder
        self.bird_feeder = BirdFeeder()
        self.bird_feeder.reroll()

        # Initialize the bird deck
        self.bird_deck = Deck()
        for bird in bird_list:
            self.bird_deck.add_card(bird)
        self.bird_deck.shuffle_deck()

        # Initialize the player hands
        #TODO: move hands outside of game state, similar to food supplies
        for player in range(num_players):
            hand = self.game_state.get_player_bird_hand(player)
            for _ in range(num_starting_cards):
                hand.add_card(self.bird_deck.draw_card())

        # Initialize the player food supplies
        self.food_supplies = [FoodSupply() for _ in range(num_players)]
        for player in range(num_players):
            starting_food = TOTAL_ALLOWED_IN_STARTING_HAND - len(self.game_state.get_player_bird_hand(player))
            self.food_supplies[player].increment(starting_food)

        # Initialize the bird tray
        self.bird_tray = Tray()
        self.bird_tray.flush(discard_pile=self.discard_pile, bird_deck=self.bird_deck)
        
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
    game.setup(NUM_PLAYERS, NUM_TURNS)
    game.play()
