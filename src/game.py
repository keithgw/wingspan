from src.entities.game_state import GameState
from src.entities.gameboard import GameBoard
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.entities.food_supply import FoodSupply
from src.entities.player import Player

# Constants
TOTAL_ALLOWED_IN_STARTING_HAND = 5
NUM_PLAYERS = 1 #TODO: get thse from STDIN
NUM_TURNS = 10

class WingspanGame:
    def __init__(self):
        self.discard_pile = Deck()
        self.actions = ["play_a_bird", "gain_food", "draw_bird_cards"] # lay_eggs not implemented yet

    def setup(self, num_turns, num_players, num_starting_cards=2):
        # Initizialize the game state, this handles turns and assigns empty player hands
        self.game_state = GameState(num_turns=num_turns, num_players=num_players)

        # Initialize the bird feeder
        self.bird_feeder = BirdFeeder()
        self.bird_feeder.reroll()

        # Initialize the bird deck
        self.bird_deck = Deck()
        for bird in bird_list:
            self.bird_deck.add_card(bird)
        self.bird_deck.shuffle_deck()

        # Initialize the players
        self.players = [None] * num_players
        for player in range(num_players):
            # deal hand
            hand = BirdHand()
            for _ in range(num_starting_cards):
                bird = self.bird_deck.draw_card()
                hand.add_card(bird, bird.get_name())
            # distribute food
            food_supply = FoodSupply()
            starting_food = TOTAL_ALLOWED_IN_STARTING_HAND - len(hand.get_cards_in_hand())
            food_supply.increment(starting_food)
            # create player
            self.players[player] = Player(hand, food_supply, self.actions)

        # Initialize the bird tray
        self.tray = Tray()
        self.tray.flush(discard_pile=self.discard_pile, bird_deck=self.bird_deck)
    
    def determine_player_turn(self):
        # Determine the current player's turn
        return self.game_state.get_current_player()
        
    def play(self):
        # Main game loop
        while not self.is_game_over():
            current_player = self.determine_player_turn()
            self.take_turn(current_player)
            self.update_game_state()
            self.render()

    def take_turn(self, player):
        # Logic for a single player's turn
        # self.players[player].request_action(bird_hand=self.bird_hands[player], food_supply=self.food_supplies[player], game_state=self.game_state, bird_feeder=self.bird_feeder, tray=self.tray, bird_deck=self.bird_deck, actions=self.actions)
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