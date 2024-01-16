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
NUM_PLAYERS = 1 #TODO: get these from STDIN
NUM_TURNS = 10

class WingspanGame:
    def __init__(self):
        self.discard_pile = Deck()

    def setup(self, num_turns, num_players, num_starting_cards=2):
        # Initizialize the game state, this tracks the current turn and player
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
            player_name = "Player " + str(player + 1)
            self.players[player] = Player(name=player_name, bird_hand=hand, food_supply=food_supply, num_turns=num_turns)

        # Initialize the bird tray
        self.tray = Tray()
        self.tray.flush(discard_pile=self.discard_pile, bird_deck=self.bird_deck)
    
    def take_turn(self, player):
        # Logic for a single player's turn
        
        # Choose an action
        chosen_action = player.request_action(tray=self.tray, bird_deck=self.bird_deck)

        # Player takes the action, which will update the feeder, tray, deck, player's game board, player's hand, and player's food supply
        player.take_action(chosen_action, tray=self.tray, bird_deck=self.bird_deck, bird_feeder=self.bird_feeder)

        # End the turn, this updates the game state and player's turn count
        self.game_state.end_player_turn(player=player, tray=self.tray, bird_deck=self.bird_deck)

    def render(self, current_player_idx):
        current_player = self.players[current_player_idx]
        # Render the current game state
        self.bird_feeder.render()
        print("Tray: ")
        self.tray.render()
        print("It is " + current_player.get_name() + "'s turn.")
        player_turns_remaining = current_player.get_turns_remaining()
        if player_turns_remaining == 1:
            print("1 turn remaining.")
        else:
            print(str(player_turns_remaining) + " turns remaining.")
        print(current_player.get_name() + "'s board: ")
        current_player.game_board.render()
        print(current_player.get_name() + "'s food supply: ")
        current_player.food_supply.render()
        print(current_player.get_name() + "'s hand: ")
        current_player.bird_hand.render()

    def get_player_scores(self):
        # Get the scores of all players
        return [player.get_score() for player in self.players]
    
    def determine_winners(self):
        '''Returns a list of player indices that are tied for the highest score'''
        # Determine the winner of the game
        scores = self.get_player_scores()

        return [player_idx for player_idx, score in enumerate(scores) if score == max(scores)]

    def render_game_summary(self):
        '''Prints the final scores and the winner(s)'''
        scores = self.get_player_scores()
        winner_idx = self.determine_winners() # list of player indices that are tied for the highest score

        # check for tie
        num_winners = len(winner_idx)
        if num_winners > 1:
            print(f"It's a {num_winners}-way tie between {', '.join([self.players[idx].get_name() for idx in winner_idx])}")
        else:
            print(self.players[winner_idx[0]].get_name() + " wins!")

        print("Final scores:")
        for player_idx, score in enumerate(scores):
            print(self.players[player_idx].get_name() + ": " + str(score))
            self.players[player_idx].game_board.render()

    def play(self):
        # Main game loop
        while not self.game_state.is_game_over():
            current_player_idx = self.game_state.get_current_player()
            self.render(current_player_idx)
            current_player = self.players[current_player_idx]
            self.take_turn(current_player)

            # Game is over, give a game summary
            self.render_game_summary()

if __name__ == "__main__":
    game = WingspanGame()
    game.setup(num_turns=NUM_TURNS, num_players=NUM_PLAYERS)
    game.play()