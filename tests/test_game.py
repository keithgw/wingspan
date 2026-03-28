import unittest
from unittest.mock import patch

from data.bird_list import birds as bird_list
from src.entities.player import BotPlayer, HumanPlayer
from src.game import WingspanGame


class TestWingspanGame(unittest.TestCase):
    def setUp(self):
        self.num_players = 2
        self.num_turns = 5
        self.num_starting_cards = 3
        self.game = WingspanGame(
            num_players=self.num_players,
            num_human=0,
            num_turns=self.num_turns,
            num_starting_cards=self.num_starting_cards,
        )

    def test_setup_invalid_num_human(self):
        with self.assertRaises(ValueError):
            WingspanGame(num_players=2, num_human=3)

    def test_setup_invalid_num_players(self):
        with self.assertRaises(ValueError):
            WingspanGame(num_players=0)

    def test_setup_invalid_num_turns(self):
        with self.assertRaises(ValueError):
            WingspanGame(num_turns=0)

    def test_setup_invalid_num_starting_cards(self):
        with self.assertRaises(ValueError):
            WingspanGame(num_starting_cards=-1)

    def test_setup_valid_inputs(self):
        gs = self.game.game_state
        players = gs.get_players()
        self.assertEqual(gs.num_players, self.num_players)
        self.assertEqual(gs.num_turns, self.num_turns)
        self.assertEqual(len(players), self.num_players)
        self.assertEqual(len(players[0].bird_hand.get_cards_in_hand()), self.num_starting_cards)
        self.assertEqual(len(players[1].bird_hand.get_cards_in_hand()), self.num_starting_cards)
        self.assertEqual(players[0].name, "Bot 1")
        self.assertEqual(players[1].name, "Bot 2")

    def test_num_cards_in_deck_and_discard_pile(self):
        gs = self.game.game_state
        num_cards_in_tray = 3
        cards_left = len(bird_list) - self.num_players * self.num_starting_cards - num_cards_in_tray
        self.assertEqual(gs.get_bird_deck().get_count(), cards_left)
        self.assertEqual(gs.get_discard_pile().get_count(), 0)

    def test_get_player_scores(self):
        self.assertEqual(self.game.get_player_scores(), [0] * self.num_players)

    def test_determine_winners_tie(self):
        self.assertEqual(self.game.determine_winners(), [0, 1])

    def test_determine_winners_winner(self):
        self.game.game_state.get_players()[0].score = 100
        self.assertEqual(self.game.determine_winners(), [0])

    @patch("builtins.input", return_value="Player Name")
    def test_human_setup(self, mock_input):
        game = WingspanGame(num_players=1, num_human=1)
        player = game.game_state.get_players()[0]
        self.assertEqual(player.name, "Player Name")
        self.assertIsInstance(player, HumanPlayer)

    def test_bot_setup(self):
        game = WingspanGame(num_players=1, num_human=0)
        player = game.game_state.get_players()[0]
        self.assertEqual(player.name, "Bot 1")
        self.assertIsInstance(player, BotPlayer)


if __name__ == "__main__":
    unittest.main()
