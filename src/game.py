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
    """Orchestrates a game of Wingspan: setup, turn loop, rendering, and scoring."""

    def __init__(
        self,
        game_state=None,
        num_players=DEFAULT_NUM_PLAYERS,
        num_human=DEFAULT_NUM_HUMAN,
        num_turns=DEFAULT_NUM_TURNS,
        num_starting_cards=DEFAULT_NUM_STARTING_CARDS,
        bot_policy_factory=None,
        advisor=None,
    ):
        if game_state is None:
            self.game_state = self._initialize_game_state(
                num_players=num_players,
                num_human=num_human,
                num_turns=num_turns,
                num_starting_cards=num_starting_cards,
                bot_policy_factory=bot_policy_factory,
                advisor=advisor,
            )
        else:
            self.game_state = game_state

    def _initialize_game_state(
        self, num_players, num_human, num_turns, num_starting_cards, bot_policy_factory, advisor=None
    ):
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
                    advisor=advisor,
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

    def _take_turn(self, player):
        chosen_action = player.request_action(game_state=self.game_state)
        player.take_action(action=chosen_action, game_state=self.game_state)
        self.game_state.end_player_turn(player=player)
        return chosen_action

    def _round_number(self):
        return self.game_state.game_turn // self.game_state.num_players + 1

    def _render(self, current_player, bot_actions=None):
        from src.utilities.utils import clear_screen, render_bird_container, render_header

        clear_screen()

        name = current_player.get_name()
        turns_left = current_player.get_turns_remaining()
        round_num = self._round_number()

        turns_word = "turn" if turns_left == 1 else "turns"
        print(f"\n  WINGSPAN  ·  Round {round_num}  ·  {name}'s turn  ·  {turns_left} {turns_word} left\n")

        # Show what bots did since the last human turn
        if bot_actions:
            for bot_name, action in bot_actions:
                print(f"  {bot_name} chose to {action.replace('_', ' ')}.")
            print()

        print(render_header("Bird Feeder"))
        print(f"  Food available: {self.game_state.get_bird_feeder().food_count}\n")

        print(render_header("Tray"))
        print(
            render_bird_container(
                self.game_state.get_tray().get_birds_in_tray(),
                capacity=self.game_state.get_tray().capacity,
            )
        )

        # Show opponent boards
        opponents = [p for p in self.game_state.get_players() if p is not current_player]
        for opp in opponents:
            opp_birds = opp.get_game_board().get_birds()
            opp_score = opp.get_score()
            opp_food = opp.get_food_supply().amount
            print(render_header(f"{opp.get_name()} — {opp_score} pts, {opp_food} food"))
            print(render_bird_container(opp_birds, capacity=opp.get_game_board().capacity))

        print(render_header(f"{name}'s Board"))
        board = current_player.get_game_board()
        print(render_bird_container(board.get_birds(), capacity=board.capacity))

        print(render_header(f"{name}'s Hand"))
        print(render_bird_container(current_player.get_bird_hand().get_cards_in_hand()))

        food = current_player.get_food_supply().amount
        score = current_player.get_score()
        print(f"  Food: {food}  ·  Score: {score}\n")

    def get_player_scores(self):
        return [player.get_score() for player in self.game_state.get_players()]

    def determine_winners(self):
        """Returns a list of player indices that are tied for the highest score"""
        scores = self.get_player_scores()
        return [player_idx for player_idx, score in enumerate(scores) if score == max(scores)]

    def _render_game_summary(self):
        from src.utilities.utils import clear_screen, render_bird_container, render_header

        clear_screen()
        scores = self.get_player_scores()
        winner_idx = self.determine_winners()

        print(f"\n{'=' * 40}")
        print("  GAME OVER")
        print(f"{'=' * 40}\n")

        num_winners = len(winner_idx)
        if num_winners > 1:
            names = ", ".join([self.game_state.get_player(idx).get_name() for idx in winner_idx])
            print(f"  It's a {num_winners}-way tie between {names}!\n")
        else:
            print(f"  {self.game_state.get_player(winner_idx[0]).get_name()} wins!\n")

        for player_idx, score in enumerate(scores):
            player = self.game_state.get_player(player_idx)
            print(render_header(f"{player.get_name()} — {score} points"))
            print(render_bird_container(player.get_game_board().get_birds()))

    def play(self):
        from src.entities.player import HumanPlayer

        bot_actions = []

        while not self.game_state.is_game_over():
            current_player = self.game_state.get_current_player()
            is_human = isinstance(current_player, HumanPlayer)

            if is_human:
                self._render(current_player, bot_actions=bot_actions)
                bot_actions = []

            action = self._take_turn(current_player)

            if not is_human:
                bot_actions.append((current_player.get_name(), action))

        if any(isinstance(p, HumanPlayer) for p in self.game_state.get_players()):
            self._render_game_summary()


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
        choices=["random", "mcts", "learned"],
        help="Bot policy: 'random', 'mcts', or 'learned' (requires --policy_path)",
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

    parser.add_argument(
        "--policy_path",
        type=str,
        default=None,
        help="Path to a trained policy file (required with --policy learned)",
    )
    parser.add_argument(
        "--hints",
        type=str,
        default=None,
        help="Path to a trained policy file to show decision hints for human players",
    )

    args = parser.parse_args()

    # Load advisor for human player hints
    advisor = None
    if args.hints:
        import os

        from src.rl.linear_policy import LinearPolicy as AdvisorPolicy

        if not os.path.exists(args.hints):
            parser.error(f"Hints policy file not found: {args.hints}")
        advisor = AdvisorPolicy.load(args.hints)

    bot_policy_factory = None
    if args.policy == "mcts":
        from src.rl.policy import MCTSPolicy

        num_sims = args.num_simulations
        bot_policy_factory = lambda: MCTSPolicy(num_simulations=num_sims)  # noqa: E731
    elif args.policy == "learned":
        import os

        from src.rl.linear_policy import LinearPolicy

        if not args.policy_path:
            parser.error("--policy_path is required when using --policy learned")
        if not os.path.exists(args.policy_path):
            parser.error(f"Policy file not found: {args.policy_path}")
        policy_path = args.policy_path
        bot_policy_factory = lambda: LinearPolicy.load(policy_path)  # noqa: E731

    game = WingspanGame(
        num_players=args.num_players,
        num_human=args.num_human,
        num_turns=args.num_turns,
        num_starting_cards=args.num_starting_cards,
        bot_policy_factory=bot_policy_factory,
        advisor=advisor,
    )
    game.play()
