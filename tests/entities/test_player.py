import unittest
from io import StringIO
from unittest.mock import Mock, patch

from src.entities.bird import Bird
from src.entities.birdfeeder import BirdFeeder
from src.entities.deck import Deck
from src.entities.food_supply import FoodSupply
from src.entities.game_state import GameState
from src.entities.gameboard import GameBoard
from src.entities.hand import BirdHand
from src.entities.player import BotPlayer, HumanPlayer, Player
from src.entities.tray import Tray
from src.rl.policy import RandomPolicy


class TestPlayerBase(unittest.TestCase):
    def setUp(self):
        self.name = "Test Player"
        self.num_turns = 5
        self.bird_hand = BirdHand()
        self.birds = [
            Bird("Osprey", 5, 1),
            Bird("Bald Eagle", 9, 3),
            Bird("Peregrine Falcon", 5, 2),
        ]
        for bird in self.birds:
            self.bird_hand.add_card(bird, bird.get_name())
        self.food_supply = FoodSupply(2)
        self.tray = Tray()
        self.bird_deck = Deck(
            cards=[
                Bird("Anhinga", 6, 2),
                Bird("Barred Owl", 3, 1),
                Bird("Willet", 4, 1),
                Bird("Carolina Chickadee", 2, 1),
            ]
        )
        self.bird_feeder = BirdFeeder(food_count=5)
        self.discard_pile = Deck()
        self.game_state = GameState(
            num_turns=self.num_turns,
            bird_deck=self.bird_deck,
            discard_pile=self.discard_pile,
            tray=self.tray,
            bird_feeder=self.bird_feeder,
            players=[None],  # placeholder, overridden in subclass setUp
        )


class TestPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.player = Player(
            name=self.name,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            num_turns_remaining=self.num_turns,
        )
        self.game_state.players = [self.player]

    def test_get_name(self):
        self.assertEqual(self.player.get_name(), "Test Player")

    def test_set_name(self):
        self.player.set_name("New Name")
        self.assertEqual(self.player.get_name(), "New Name")

    def test_get_bird_hand(self):
        self.assertEqual(self.player.get_bird_hand(), self.bird_hand)

    def test_get_food_supply(self):
        self.assertEqual(self.player.get_food_supply(), self.food_supply)

    def test_get_game_board(self):
        game_board = GameBoard()
        self.player.game_board = game_board
        self.assertEqual(self.player.get_game_board(), game_board)

    def test_init_with_game_board(self):
        board = GameBoard(capacity=3)
        player = Player("P", BirdHand(), FoodSupply(), num_turns_remaining=5, game_board=board)
        self.assertIs(player.get_game_board(), board)

    def test_enumerate_playable_birds(self):
        playable = self.player._enumerate_playable_birds()
        # Osprey costs 1 (affordable), Bald Eagle costs 3 (not), Peregrine costs 2 (affordable)
        self.assertIn("Osprey", playable)
        self.assertIn("Peregrine Falcon", playable)
        self.assertNotIn("Bald Eagle", playable)

    def test_enumerate_legal_actions(self):
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)

        # Player has birds in hand and sufficient food to play at least one
        self.assertIn("play_a_bird", legal_actions)

        # Player cannot play a bird, insufficient food
        self.player.food_supply.decrement(2)
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)
        self.assertNotIn("play_a_bird", legal_actions)

        # Player should always be able to gain food
        self.assertIn("gain_food", legal_actions)

        # Player should be able to draw a bird from non-empty deck
        self.assertIn("draw_a_bird", legal_actions)

        # Player cannot draw when deck and tray both empty
        empty_tray = Tray()
        empty_deck = Deck()
        legal_actions = self.player._enumerate_legal_actions(empty_tray, empty_deck)
        self.assertNotIn("draw_a_bird", legal_actions)

    @patch.object(Player, "_choose_action", return_value="play_a_bird")
    def test_request_action(self, choose_action_mock):
        action = self.player.request_action(game_state=self.game_state)
        choose_action_mock.assert_called_once()
        self.assertEqual(action, "play_a_bird")

    def test_take_action_invalid(self):
        with self.assertRaises(Exception):
            self.player.take_action("invalid_action", game_state=self.game_state)

    def test_take_action_play_a_bird(self):
        with patch.object(Player, "play_a_bird") as mock:
            self.player.take_action("play_a_bird", game_state=self.game_state)
            mock.assert_called_once()

    def test_take_action_gain_food(self):
        with patch.object(Player, "gain_food") as mock:
            self.player.take_action("gain_food", game_state=self.game_state)
            mock.assert_called_once()

    def test_take_action_draw_a_bird(self):
        with patch.object(Player, "draw_a_bird") as mock:
            self.player.take_action("draw_a_bird", game_state=self.game_state)
            mock.assert_called_once()

    def test_play_a_bird(self):
        bird = self.birds[0]
        bird_name = bird.get_name()
        initial_food = self.player.food_supply.amount
        with patch.object(self.player, "_choose_a_bird_to_play", return_value=bird_name):
            self.player.play_a_bird(game_state=self.game_state)

        self.assertNotIn(bird, self.player.bird_hand.get_cards_in_hand())
        self.assertIn(bird, self.player.game_board.get_birds())
        self.assertEqual(self.player.food_supply.amount, initial_food - bird.get_food_cost())

    def test_gain_food(self):
        bird_feeder = BirdFeeder(food_count=5)
        self.player.gain_food(bird_feeder)
        self.assertEqual(self.player.food_supply.amount, 3)
        self.assertEqual(bird_feeder.food_count, 4)

    def test_draw_a_bird_from_deck(self):
        with patch.object(self.player, "_choose_a_bird_to_draw", return_value="deck"):
            self.player.draw_a_bird(game_state=self.game_state)
            self.assertIn("Anhinga", self.player.bird_hand.get_card_names_in_hand())

    def test_end_turn(self):
        initial_turns = self.player.get_turns_remaining()
        self.player.end_turn()
        self.assertEqual(self.player.turns_remaining, initial_turns - 1)

        self.player.game_board.add_bird(self.birds[0])
        self.player.end_turn()
        self.assertEqual(self.player.score, self.birds[0].get_points())

    def test_get_turns_remaining(self):
        self.assertEqual(self.player.get_turns_remaining(), self.num_turns)


class TestHumanPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.player = HumanPlayer(
            name=self.name,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            num_turns_remaining=self.num_turns,
        )
        self.game_state.players = [self.player]

    @patch("builtins.input", return_value="1")
    def test_choose_action(self, mock_input):
        legal_actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        action = self.player._choose_action(legal_actions=legal_actions, game_state=self.game_state)
        self.assertEqual(action, "play_a_bird")

    @patch("builtins.input", return_value="Osprey")
    def test_choose_a_bird_to_play(self, mock_input):
        playable = self.player._enumerate_playable_birds()
        bird = self.player._choose_a_bird_to_play(playable_birds=playable, game_state=self.game_state)
        self.assertEqual(bird, "Osprey")

    @patch("builtins.input", return_value="deck")
    def test_choose_a_bird_to_draw(self, mock_input):
        valid_choices = self.tray.see_birds_in_tray() + ["deck"]
        choice = self.player._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=self.game_state)
        self.assertEqual(choice, "deck")


class TestHumanPlayerAdvisor(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.advisor = Mock()
        self.player = HumanPlayer(
            name=self.name,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            num_turns_remaining=self.num_turns,
            advisor=self.advisor,
        )
        self.game_state.players = [self.player]

    @patch("builtins.input", return_value="2")
    def test_action_hints_displayed(self, mock_input):
        import numpy as np

        self.advisor.get_action_probabilities.return_value = np.array([0.7, 0.2, 0.1])
        captured = StringIO()
        with patch("sys.stdout", captured):
            self.player._choose_action(
                legal_actions=["play_a_bird", "gain_food", "draw_a_bird"],
                game_state=self.game_state,
            )
        output = captured.getvalue()
        self.assertIn("Advisor suggests (Action):", output)
        self.assertIn("play a bird", output)
        self.assertIn("70.0%", output)
        self.assertIn("*", output)

    @patch("builtins.input", return_value="Osprey")
    def test_bird_to_play_hints_displayed(self, mock_input):
        import numpy as np

        self.advisor.get_action_probabilities.return_value = np.array([0.8, 0.2])
        captured = StringIO()
        with patch("sys.stdout", captured):
            self.player._choose_a_bird_to_play(
                playable_birds=["Osprey", "Cardinal"],
                game_state=self.game_state,
            )
        output = captured.getvalue()
        self.assertIn("Advisor suggests (Bird to play):", output)
        self.assertIn("Osprey", output)
        self.assertIn("80.0%", output)

    @patch("builtins.input", return_value="deck")
    def test_bird_to_draw_hints_displayed(self, mock_input):
        import numpy as np

        self.advisor.get_action_probabilities.return_value = np.array([0.3, 0.3, 0.4])
        captured = StringIO()
        with patch("sys.stdout", captured):
            self.player._choose_a_bird_to_draw(
                valid_choices=["Blue Jay", "Cardinal", "deck"],
                game_state=self.game_state,
            )
        output = captured.getvalue()
        self.assertIn("Advisor suggests (Bird to draw):", output)
        self.assertIn("deck", output)
        self.assertIn("40.0%", output)

    def test_no_advisor_no_output(self):
        player_no_advisor = HumanPlayer(
            name="No Hints",
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            num_turns_remaining=self.num_turns,
        )
        captured = StringIO()
        with patch("sys.stdout", captured):
            player_no_advisor._show_hints(self.game_state, ["gain_food"])
        self.assertEqual(captured.getvalue(), "")


class TestBotPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.player = BotPlayer(
            policy=RandomPolicy(),
            name=self.name,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            num_turns_remaining=self.num_turns,
        )
        self.game_state.players = [self.player]

    def test_choose_action(self):
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)
        action = self.player._choose_action(legal_actions=legal_actions, game_state=self.game_state)
        self.assertIn(action, legal_actions)

    def test_choose_a_bird_to_play(self):
        playable = self.player._enumerate_playable_birds()
        bird = self.player._choose_a_bird_to_play(playable_birds=playable, game_state=self.game_state)
        self.assertIn(bird, self.player.bird_hand.get_card_names_in_hand())

    def test_choose_a_bird_to_draw(self):
        valid_choices = self.tray.see_birds_in_tray() + ["deck"]
        choice = self.player._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=self.game_state)
        self.assertIn(choice, valid_choices)


if __name__ == "__main__":
    unittest.main()
