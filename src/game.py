from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.player import Player
from src.entities.game_state import GameState
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from data.bird_list import birds as bird_list
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.entities.food_supply import FoodSupply
from argparse import ArgumentParser

# Constants #TODO: move to a config file
TOTAL_ALLOWED_IN_STARTING_HAND = 5
DEFAULT_NUM_PLAYERS = 2
DEFAULT_NUM_HUMAN = 0
DEFAULT_NUM_TURNS = 10
DEFAULT_NUM_STARTING_CARDS = 2

class WingspanGame:
    def __init__(self, 
                    game_state: Optional[GameState] = None,
                    num_players: int = DEFAULT_NUM_PLAYERS, 
                    num_human: int = DEFAULT_NUM_HUMAN, 
                    num_turns: int = DEFAULT_NUM_TURNS, 
                    num_starting_cards: int = DEFAULT_NUM_STARTING_CARDS) -> None:
        """
        Initializes a game instance with an optional game state. 
        If no game state provided, initializes a new game state with the given parameters.
        If a game state is provided, the initialization parameters are ignored.

        Args:
            game_state (GameState, optional): The initial game state. Defaults to None.
            num_players (int, optional): The total number of players. Defaults to DEFAULT_NUM_PLAYERS.
            num_human (int, optional): The number of human players. Defaults to DEFAULT_NUM_HUMAN.
            num_turns (int, optional): The number of turns for each player. Defaults to DEFAULT_NUM_TURNS.
            num_starting_cards (int, optional): The number of starting cards for each player. Defaults to DEFAULT_NUM_STARTING_CARDS.

        Raises:
            ValueError: If the number of human players exceeds the total number of players,
                        or if the number of players is less than 1,
                        or if the number of turns is less than 1,
                        or if the number of starting cards is negative.
        """
        if game_state is None:
            # Initialize the game state
            self.game_state = self._initialize_game_state(num_players=num_players, num_human=num_human, num_turns=num_turns, num_starting_cards=num_starting_cards)
        else:
            self.game_state = game_state

    def _initialize_game_state(self, num_players: int, num_human: int, num_turns: int, num_starting_cards: int) -> GameState:
        """
        Initializes the game state by setting up the bird feeder, bird deck, discard pile, players, and bird tray.

        Args:
            num_players (int): The total number of players.
            num_human (int): The number of human players. num_bot = num_players - num_human
            num_turns (int): The number of turns for each player.
            num_starting_cards (int): The number of starting cards for each player.
        Returns:
            GameState: The initialized game state.
        """
        # Import here to avoid circular imports
        from src.utilities.player_factory import create_human_player, create_bot_player
        
        # Validate inputs
        if num_human > num_players:
            raise ValueError("Number of human players cannot exceed total number of players.")
        elif num_players < 1:
            raise ValueError("Number of players must be at least 1.")
        elif num_turns < 1:
            raise ValueError("Number of turns must be at least 1.")
        elif num_starting_cards < 0:
            raise ValueError("Number of starting cards cannot be negative.")
        
        # Initialize the bird feeder
        bird_feeder = BirdFeeder()
        bird_feeder.reroll()

        # Initialize the bird deck and discard pile
        bird_deck = Deck()
        bird_deck.prepare_deck(cards=bird_list)
        discard_pile = Deck()

        # Initialize the players
        players = [None] * num_players
        turn_order = ['human'] * num_human + ['bot'] * (num_players - num_human) # TODO: make this randomizable or settable

        # set up each player
        for player in range(num_players):
            # deal hand
            hand = BirdHand()
            for _ in range(num_starting_cards):
                bird = bird_deck.draw_card()
                hand.add_card(bird, bird.get_name())

            # distribute food
            food_supply = FoodSupply()
            starting_food = TOTAL_ALLOWED_IN_STARTING_HAND - len(hand.get_cards_in_hand())
            food_supply.increment(starting_food)

            # create player
            if turn_order[player] == 'human':
                player_name = input(f"What is Player {player + 1}'s name? ")
                players[player] = create_human_player(name=player_name, bird_hand=hand, food_supply=food_supply, num_turns=num_turns)
            else:
                player_name = f"Bot {player + 1}"
                players[player] = create_bot_player(name=player_name, bird_hand=hand, food_supply=food_supply, num_turns=num_turns)

        # Initialize the bird tray
        tray = Tray()
        tray.flush(discard_pile=discard_pile, bird_deck=bird_deck)
        #TODO: for each BotPlayer, update their known_missing_cards set with the cards in the tray

        # Initizialize the game state, this tracks the current turn and player
        return GameState(
            num_turns=num_turns,
            bird_deck=bird_deck,
            discard_pile=discard_pile,
            tray=tray,
            bird_feeder=bird_feeder,
            players=players
        )
    
    def set_game_state(self, game_state: GameState) -> None:
            """
            Public method to set the game state.

            Args:
                game_state (GameState): The new game state.

            Returns:
                None
            """
            self.game_state = game_state

    def take_turn(self, player: 'Player') -> None:
        """
        Logic for a single player's turn. This will have the player choose an action, take the action, and end the turn.
        The game state will be updated as a side effect of the player taking an action and explicitly at the end of the turn.

        Args:
            player (Player): The player whose turn it is.
        """
        # Choose an action
        chosen_action = player.request_action(game_state=self.game_state)

        # Update the game phase based on the chosen action
        self.game_state.update_game_phase(action=chosen_action)

        # Player takes the action, which will update the feeder, tray, deck, player's game board, player's hand, and player's food supply
        player.take_action(action=chosen_action, game_state=self.game_state)

        # End the turn, this refills the tray if necessary, increments the turn counter, and calls player.end_turn()
        self.game_state.end_player_turn(player=player)

    def render(self, current_player: 'Player') -> None:
        """
        Renders the current game state.
        
        Args:
            current_player (Player): The player whose turn it is.
        """
        # Render the global game state
        self.game_state.get_bird_feeder().render()
        print("Tray: ")
        self.game_state.get_tray().render()

        # Render the current player's state
        print("It is " + current_player.get_name() + "'s turn.")
        player_turns_remaining = current_player.get_turns_remaining()
        if player_turns_remaining == 1:
            print("1 turn remaining.")
        else:
            print(str(player_turns_remaining) + " turns remaining.")
        print(current_player.get_name() + "'s board: ")
        current_player.get_game_board().render()
        print(current_player.get_name() + "'s food supply: ")
        current_player.get_food_supply().render()
        print(current_player.get_name() + "'s hand: ")
        current_player.get_bird_hand().render()

        #TODO: render a representation of the opponent boards, hands, and food supplies

    def get_player_scores(self) -> list: #TODO: move to GameState
        """Returns a list of player scores indexed by initial turn order"""
        return [player.get_score() for player in self.game_state.get_players()]
    
    def determine_winners(self) -> list: #TODO: move to GameState
        """Returns a list of player indices that are tied for the highest score"""
        # Determine the winner of the game
        scores = self.get_player_scores()

        return [player_idx for player_idx, score in enumerate(scores) if score == max(scores)]

    def render_game_summary(self) -> None:
        """Prints the final scores and the winner(s)"""
        scores = self.get_player_scores() #TODO: get from GameState
        winner_idx = self.determine_winners() # list of player indices that are tied for the highest score #TODO: Get from GameState

        # check for tie
        num_winners = len(winner_idx)
        if num_winners > 1:
            print(f"It's a {num_winners}-way tie between {', '.join([self.game_state.get_player(idx).get_name() for idx in winner_idx])}")
        else:
            print(self.game_state.get_player(winner_idx[0]).get_name() + " wins!")

        print("Final scores:")
        for player_idx, score in enumerate(scores):
            print(self.game_state.get_player(player_idx).get_name() + ": " + str(score))
            self.game_state.get_player(player_idx).get_game_board().render()

    def play(self):
        # Main game loop
        while not self.game_state.is_game_over():
            current_player = self.game_state.get_current_player()
            self.render(current_player) #TODO: make optional
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

    game = WingspanGame(
        num_players=args.num_players,
        num_human=args.num_human,
        num_turns=args.num_turns,
        num_starting_cards=args.num_starting_cards
    )
    game.play()