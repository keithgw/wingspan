import unittest
from src.game import WingspanGame
from data.bird_list import birds as bird_list
from unittest.mock import patch, Mock
from src.entities.player import Player, HumanPlayer, BotPlayer

class TestWingspanGame(unittest.TestCase):
    def setUp(self):
        self.game = WingspanGame(num_players=4, num_human=0, num_turns=10, num_starting_cards=5)

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

    def test_new_game_state_set_by_default(self):
        game = WingspanGame(game_state=None)
        self.assertIsNotNone(game.game_state)

    def test_passed_game_state_set(self):
        game_state = Mock()
        game = WingspanGame(game_state=game_state)
        self.assertEqual(game.game_state, game_state)

    @patch('builtins.input', return_value='Human Adult Person')
    def test_initialize_game_state(self, input):
        num_players = 3
        num_human = 1
        num_turns = 10
        num_starting_cards = 5

        game_state = self.game._initialize_game_state(num_players, num_human, num_turns, num_starting_cards)

        # global game state assertions
        self.assertEqual(game_state.bird_feeder.food_count, 5)
        self.assertEqual(game_state.bird_deck.get_count(), len(bird_list) - num_players * num_starting_cards - 3)
        self.assertEqual(game_state.discard_pile.get_count(), 0)
        self.assertEqual(game_state.num_players, num_players)
        self.assertEqual(game_state.num_turns, num_turns)
        self.assertEqual(game_state.tray.get_count(), 3)

        # player-specific assertions
        for player_idx in range(num_players):
            player = game_state.players[player_idx]
            self.assertEqual(len(player.bird_hand.get_cards_in_hand()), num_starting_cards)
            self.assertEqual(player.food_supply.amount, 5 - num_starting_cards)
            if player_idx == 0:
                self.assertIsInstance(player, HumanPlayer)
                self.assertEqual(player.name, "Human Adult Person")
            else:
                self.assertIsInstance(player, BotPlayer)
                self.assertEqual(player.name, "Bot {}".format(player_idx + 1))

    def test_set_game_state(self):
        game_state = Mock()
        self.game.set_game_state(game_state)
        self.assertEqual(self.game.game_state, game_state)

    def test_get_player_scores(self):
        # Assertions to test the scoring of the game object
        self.assertEqual(self.game.get_player_scores(), [0] * self.game.game_state.num_players)

    def test_determine_winners_there_is_a_tie(self):
        # Assertions to test the determination of winners
        # All players have a score of 0, so all should be declared the winner
        self.assertEqual(self.game.determine_winners(), list(range(self.game.game_state.num_players)))

    def test_determine_winners_there_is_a_winner(self):
        # Assertions to test the determination of winners
        self.game.game_state.players[0].score = 100
        self.assertEqual(self.game.determine_winners(), [0])

    def test_take_turn(self):
        # Assertions to test the taking of a turn
        # Create a mock Player object
        mock_player = Mock(spec=Player)
        mock_player.request_action.return_value = 'gain_food'

        # Create a mock GameState object
        mock_game_state = Mock()
        
        # Create a WingspanGame object with the mock GameState
        game = WingspanGame(mock_game_state)

        # Call the method to test
        game.take_turn(mock_player)

        # Check if the methods were called correctly
        mock_player.request_action.assert_called_once_with(game_state=mock_game_state)
        mock_player.take_action.assert_called_once_with(action='gain_food', game_state=mock_game_state)
        mock_game_state.end_player_turn.assert_called_once_with(player=mock_player)
        
if __name__ == "__main__":
    unittest.main()