import unittest
from src.entities.game_state import GameState
from src.entities.player import Player
from src.entities.hand import BirdHand
from src.entities.food_supply import FoodSupply
from src.entities.deck import Deck
from src.entities.tray import Tray
from unittest.mock import patch

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.num_turns = 10
        self.num_players = 4
        self.game_state = GameState(num_turns=self.num_turns, num_players=self.num_players)  # Example initialization with 10 turns and 4 players
        self.test_player = Player(name="Test Player", bird_hand=BirdHand(), food_supply=FoodSupply(), num_turns=self.num_turns)
        self.bird_deck = Deck()
        self.tray = Tray()

    def test_get_num_turns(self):
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_num_turns_does_not_change(self):
        self.game_state.end_player_turn(self.test_player, self.tray, self.bird_deck)
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_get_current_player(self):
        self.assertEqual(self.game_state.get_current_player(), 0)  # Assuming player indexing starts from 0

    def test_end_player_turn(self):
        with patch('src.entities.tray.Tray.refill') as mock_refill:
            self.game_state.end_player_turn(player=self.test_player, tray=self.tray, bird_deck=self.bird_deck)

            # tray is empty, check that tray.refill() is called
            mock_refill.assert_called_once_with(self.bird_deck)

            # game turn increments
            self.assertEqual(self.game_state.game_turn, 1)

            # current player changes
            self.assertEqual(self.game_state.get_current_player(), 1)

            # player's turns remaining decrements
            self.assertEqual(self.test_player.get_turns_remaining(), self.num_turns - 1)

    def test_is_game_over(self):
        self.assertFalse(self.game_state.is_game_over())
        for _ in range(self.num_players * self.num_turns):
            self.game_state.end_player_turn(player=self.test_player, tray=self.tray, bird_deck=self.bird_deck)
        self.assertTrue(self.game_state.is_game_over())

if __name__ == '__main__':
    unittest.main()