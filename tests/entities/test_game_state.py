import unittest
from src.entities.game_state import GameState
from src.entities.player import Player
from src.entities.hand import BirdHand
from src.entities.food_supply import FoodSupply
from src.entities.deck import Deck
from src.entities.tray import Tray
from unittest.mock import Mock

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.num_turns = 10
        self.players = [Mock(), Mock(), Mock(), Mock()]
        self.game_state = GameState(num_turns=self.num_turns, bird_deck=Mock(), discard_pile=Mock(), tray=Mock(), bird_feeder=Mock(), players=self.players)  # Example initialization with 10 turns and 4 players

    def test_get_num_turns(self):
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_get_current_player_start(self):
        self.assertEqual(self.game_state.get_current_player(), self.players[0])

    def test_get_current_player_after_one_turn(self):
        self.game_state.end_player_turn(self.players[0])
        self.assertEqual(self.game_state.get_current_player(), self.players[1])

    def test_end_player_turn_refills_tray(self):
            self.game_state.end_player_turn(player=self.players[0])

            # tray is empty, check that tray.refill() is called
            self.game_state.tray.is_not_full.return_value = True
            self.game_state.tray.refill.assert_called_once_with(self.game_state.bird_deck)

    def test_end_player_turn_increments_game_turn(self):
            self.game_state.end_player_turn(player=self.players[0])

            # game turn increments
            self.assertEqual(self.game_state.game_turn, 1)

    def test_end_player_turn_calls_player_end_turn(self):
            self.game_state.end_player_turn(player=self.players[0])

            # player.end_turn() is called
            self.players[0].end_turn.assert_called_once()

    def test_num_turns_does_not_change(self):
        self.game_state.end_player_turn(self.players[0])
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_is_game_over(self):
        for turn in range(self.num_turns):
            for i in range(self.game_state.num_players):
                self.game_state.end_player_turn(player=self.players[i])
                if turn < self.num_turns - 1 or i < self.game_state.num_players - 1:
                   self.assertFalse(self.game_state.is_game_over())
        self.assertTrue(self.game_state.is_game_over())

if __name__ == '__main__':
    unittest.main()