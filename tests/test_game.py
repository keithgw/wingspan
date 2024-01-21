import unittest
from src.game import WingspanGame
from data.bird_list import birds as bird_list
from unittest.mock import patch
from src.entities.player import HumanPlayer, BotPlayer

class TestWingspanGame(unittest.TestCase):
    def setUp(self):
        self.num_players = 2
        self.num_turns = 5
        self.num_starting_cards = 3
        self.game = WingspanGame()
        self.game.setup(num_players=self.num_players, num_human=0, num_turns=self.num_turns, num_starting_cards=self.num_starting_cards)

    def test_setup_invalid_num_human(self):
        with self.assertRaises(ValueError):
            self.game.setup(num_players=2, num_human=3)

    def test_setup_invalid_num_players(self):
        with self.assertRaises(ValueError):
            self.game.setup(num_players=0)

    def test_setup_invalid_num_turns(self):
        with self.assertRaises(ValueError):
            self.game.setup(num_turns=0)

    def test_setup_invalid_num_starting_cards(self):
        with self.assertRaises(ValueError):
            self.game.setup(num_starting_cards=-1)

    def test_setup_valid_inputs(self):
        self.assertEqual(self.game.game_state.num_players, self.num_players)
        self.assertEqual(self.game.game_state.num_turns, self.num_turns)
        self.assertEqual(len(self.game.players), self.num_players)
        self.assertEqual(len(self.game.players[0].bird_hand.get_cards_in_hand()), self.num_starting_cards)
        self.assertEqual(len(self.game.players[1].bird_hand.get_cards_in_hand()), self.num_starting_cards)
        self.assertEqual(self.game.players[0].name, "Bot 1")
        self.assertEqual(self.game.players[1].name, "Bot 2")
        
    def test_num_cards_in_deck_and_discard_pile(self):
        num_cards_in_tray = 3
        cards_left_in_deck = len(bird_list) - self.num_players * self.num_starting_cards - num_cards_in_tray
        self.assertEqual(self.game.bird_deck.get_count(), cards_left_in_deck)
        self.assertEqual(self.game.discard_pile.get_count(), 0)

    def test_get_player_scores(self):
        # Assertions to test the scoring of the game object
        self.assertEqual(self.game.get_player_scores(), [0] * self.num_players)

    def test_determine_winners_there_is_a_tie(self):
        # Assertions to test the determination of winners
        self.assertEqual(self.game.determine_winners(), [0, 1])

    def test_determine_winners_there_is_a_winner(self):
        # Assertions to test the determination of winners
        self.game.players[0].score = 100
        self.assertEqual(self.game.determine_winners(), [0])

    @patch('builtins.input', return_value='Player Name')
    def test_human_setup(self, input):
        # Assertions to test the setup of a human player
        self.game.setup(num_players=1, num_human=1)
        self.assertEqual(self.game.players[0].name, "Player Name")
        self.assertIsInstance(self.game.players[0], HumanPlayer)

    def test_bot_setup(self):
        # Assertions to test the setup of a bot player
        self.game.setup(num_players=1, num_human=0)
        self.assertEqual(self.game.players[0].name, "Bot 1")
        self.assertIsInstance(self.game.players[0], BotPlayer)
        
if __name__ == "__main__":
    unittest.main()