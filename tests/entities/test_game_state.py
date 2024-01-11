import unittest
from src.entities.game_state import GameState
from src.entities.bird import Bird

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState(num_turns=10, num_players=4)  # Example initialization with 10 turns and 4 players

    def test_get_num_turns(self):
        self.assertEqual(self.game_state.get_num_turns(), 10)

    def test_num_turns_does_not_change(self):
        self.game_state.end_player_turn()
        self.assertEqual(self.game_state.get_num_turns(), 10)

    def test_get_current_player(self):
        self.assertEqual(self.game_state.get_current_player(), 0)  # Assuming player indexing starts from 0

    def test_get_player_name(self):
        self.assertEqual(self.game_state.get_player_name(0), 'Player 1')

    def set_player_name(self):
        self.game_state.set_player_name(0, 'New Name')
        self.assertEqual(self.game_state.get_player_name(0), 'New Name')

    def test_end_player_turn(self):
        initial_turns_remaining = self.game_state.get_turns_remaining()
        self.game_state.end_player_turn()

        # total turns remain unchanged
        self.assertEqual(self.game_state.get_num_turns(), 10)

        # current player changes
        self.assertEqual(self.game_state.get_current_player(), 1)

        # turns remaining for player 0 decreases by 1, others remain unchanged
        self.assertEqual(self.game_state.get_turns_remaining(), [turn - 1 if i == 0 else turn for i, turn in enumerate(initial_turns_remaining)])

    def test_get_turns_remaining(self):
        self.assertEqual(self.game_state.get_turns_remaining(), [10] * 4)

if __name__ == '__main__':
    unittest.main()
