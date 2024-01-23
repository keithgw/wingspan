from src.entities.game_state import GameState
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.entities.food_supply import FoodSupply
from src.entities.player import HumanPlayer, BotPlayer
from argparse import ArgumentParser

# Constants
TOTAL_ALLOWED_IN_STARTING_HAND = 5
DEFAULT_NUM_PLAYERS = 2
DEFAULT_NUM_HUMAN = 0
DEFAULT_NUM_TURNS = 10
DEFAULT_NUM_STARTING_CARDS = 2

class WingspanGame:
    def __init__(self):
        self.discard_pile = Deck()

    def setup(self, 
              num_players=DEFAULT_NUM_PLAYERS, 
              num_human=DEFAULT_NUM_HUMAN, 
              num_turns=DEFAULT_NUM_TURNS, 
              num_starting_cards=DEFAULT_NUM_STARTING_CARDS):
        
        # Validate inputs
        if num_human > num_players:
            raise ValueError("Number of human players cannot exceed total number of players.")
        elif num_players < 1:
            raise ValueError("Number of players must be at least 1.")
        elif num_turns < 1:
            raise ValueError("Number of turns must be at least 1.")
        elif num_starting_cards < 0:
            raise ValueError("Number of starting cards cannot be negative.")

        # Initizialize the game state, this tracks the current turn and player
        self.game_state = GameState(num_players=num_players, num_turns=num_turns)

        # Initialize the bird feeder
        self.bird_feeder = BirdFeeder()
        self.bird_feeder.reroll()

        # Initialize the bird deck
        self.bird_deck = Deck()
        for bird in bird_list:
            self.bird_deck.add_card(bird)
        self.bird_deck.shuffle()

        # Initialize the players
        self.players = [None] * num_players
        turn_order = ['human'] * num_human + ['bot'] * (num_players - num_human) # TODO: make this randomizable or settable

        # set up each player
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
            if turn_order[player] == 'human':
                player_name = input(f"What is Player {player + 1}'s name? ")
                self.players[player] = HumanPlayer(name=player_name, bird_hand=hand, food_supply=food_supply, num_turns=num_turns)
            else:
                player_name = f"Bot {player + 1}"
                self.players[player] = BotPlayer(name=player_name, bird_hand=hand, food_supply=food_supply, num_turns=num_turns)

        # Initialize the bird tray
        self.tray = Tray()
        self.tray.flush(discard_pile=self.discard_pile, bird_deck=self.bird_deck)
        #TODO: for each BotPlayer, update their known_missing_cards set with the cards in the tray
    
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
            self.render(current_player_idx) #TODO: make optional
            current_player = self.players[current_player_idx]
            self.take_turn(current_player)

        # Game is over, give a game summary
        self.render_game_summary() #TODO: make optional

if __name__ == "__main__":
    parser = ArgumentParser(description='Set up a game of Wingspan.')
    parser.add_argument('--num_players', type=int, default=DEFAULT_NUM_PLAYERS, help='Number of players in the game')
    parser.add_argument('--num_human', type=int, default=DEFAULT_NUM_HUMAN, help='Number of human players in the game')
    parser.add_argument('--num_turns', type=int, default=DEFAULT_NUM_TURNS, help='Number of turns in the game')
    parser.add_argument('--num_starting_cards', type=int, default=DEFAULT_NUM_STARTING_CARDS, help='Number of cards in each player\'s starting hand')

    args = parser.parse_args()

    game = WingspanGame()
    game.setup(num_players=args.num_players, num_human=args.num_human, num_turns=args.num_turns, num_starting_cards=args.num_starting_cards)
    game.play()