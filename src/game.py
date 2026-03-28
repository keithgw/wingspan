import argparse
from argparse import ArgumentParser

from data.bird_list import birds as bird_list
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from src.entities.food_supply import FoodSupply
from src.entities.game_state import GameState
from src.entities.hand import BirdHand
from src.entities.tray import Tray
from src.utilities.player_factory import create_bot_player, create_human_player

# Constants
TOTAL_ALLOWED_IN_STARTING_HAND = 5
DEFAULT_NUM_PLAYERS = 2
DEFAULT_NUM_HUMAN = 0
DEFAULT_NUM_TURNS = 10
DEFAULT_NUM_STARTING_CARDS = 2


class WingspanGame:
    def __init__(
        self,
        game_state=None,
        num_players=DEFAULT_NUM_PLAYERS,
        num_human=DEFAULT_NUM_HUMAN,
        num_turns=DEFAULT_NUM_TURNS,
        num_starting_cards=DEFAULT_NUM_STARTING_CARDS,
        bot_policy_factory=None,
    ):
        if game_state is None:
            self.game_state = self._initialize_game_state(
                num_players=num_players,
                num_human=num_human,
                num_turns=num_turns,
                num_starting_cards=num_starting_cards,
                bot_policy_factory=bot_policy_factory,
            )
        else:
            self.game_state = game_state

    def _initialize_game_state(self, num_players, num_human, num_turns, num_starting_cards, bot_policy_factory):
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
        turn_order = ["human"] * num_human + ["bot"] * (num_players - num_human)

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
            if turn_order[player] == "human":
                player_name = input(f"What is Player {player + 1}'s name? ")
                players[player] = create_human_player(
                    name=player_name,
                    bird_hand=hand,
                    food_supply=food_supply,
                    num_turns_remaining=num_turns,
                )
            else:
                player_name = f"Bot {player + 1}"
                policy = bot_policy_factory() if bot_policy_factory else None
                players[player] = create_bot_player(
                    name=player_name,
                    bird_hand=hand,
                    food_supply=food_supply,
                    num_turns_remaining=num_turns,
                    policy=policy,
                )

        # Initialize the bird tray
        tray = Tray()
        tray.flush(discard_pile=discard_pile, bird_deck=bird_deck)

        return GameState(
            num_turns=num_turns,
            bird_deck=bird_deck,
            discard_pile=discard_pile,
            tray=tray,
            bird_feeder=bird_feeder,
            players=players,
        )

    def take_turn(self, player):
        chosen_action = player.request_action(game_state=self.game_state)
        player.take_action(action=chosen_action, game_state=self.game_state)
        self.game_state.end_player_turn(player=player)

    def render(self, current_player):
        self.game_state.get_bird_feeder().render()
        print("Tray: ")
        self.game_state.get_tray().render()
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

    def get_player_scores(self):
        return [player.get_score() for player in self.game_state.get_players()]

    def determine_winners(self):
        """Returns a list of player indices that are tied for the highest score"""
        scores = self.get_player_scores()
        return [player_idx for player_idx, score in enumerate(scores) if score == max(scores)]

    def render_game_summary(self):
        """Prints the final scores and the winner(s)"""
        scores = self.get_player_scores()
        winner_idx = self.determine_winners()

        num_winners = len(winner_idx)
        if num_winners > 1:
            names = ", ".join([self.game_state.get_player(idx).get_name() for idx in winner_idx])
            print(f"It's a {num_winners}-way tie between {names}")
        else:
            print(self.game_state.get_player(winner_idx[0]).get_name() + " wins!")

        print("Final scores:")
        for player_idx, score in enumerate(scores):
            print(self.game_state.get_player(player_idx).get_name() + ": " + str(score))
            self.game_state.get_player(player_idx).get_game_board().render()

    def play(self):
        while not self.game_state.is_game_over():
            current_player = self.game_state.get_current_player()
            self.render(current_player)
            self.take_turn(current_player)

        self.render_game_summary()


if __name__ == "__main__":
    parser = ArgumentParser(description="Set up a game of Wingspan.")
    parser.add_argument(
        "--num_players",
        type=int,
        default=DEFAULT_NUM_PLAYERS,
        help="Number of players in the game",
    )
    parser.add_argument(
        "--num_human",
        type=int,
        default=DEFAULT_NUM_HUMAN,
        help="Number of human players in the game",
    )
    parser.add_argument(
        "--num_turns",
        type=int,
        default=DEFAULT_NUM_TURNS,
        help="Number of turns in the game",
    )
    parser.add_argument(
        "--num_starting_cards",
        type=int,
        default=DEFAULT_NUM_STARTING_CARDS,
        help="Number of cards in each player's starting hand",
    )

    parser.add_argument(
        "--policy",
        type=str,
        default="random",
        choices=["random", "mcts"],
        help="Bot policy: 'random' (fast) or 'mcts' (smarter, slower)",
    )

    def positive_int(value):
        ivalue = int(value)
        if ivalue < 1:
            raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
        return ivalue

    parser.add_argument(
        "--num_simulations",
        type=positive_int,
        default=100,
        help="Number of MCTS simulations per decision (only used with --policy mcts)",
    )

    args = parser.parse_args()

    bot_policy_factory = None
    if args.policy == "mcts":
        from src.rl.policy import MCTSPolicy

        num_sims = args.num_simulations
        bot_policy_factory = lambda: MCTSPolicy(num_simulations=num_sims)  # noqa: E731

    game = WingspanGame(
        num_players=args.num_players,
        num_human=args.num_human,
        num_turns=args.num_turns,
        num_starting_cards=args.num_starting_cards,
        bot_policy_factory=bot_policy_factory,
    )
    game.play()
