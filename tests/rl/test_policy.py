import unittest
from unittest.mock import Mock, patch

from src.rl.policy import RandomPolicy


class TestRandomPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomPolicy()

    @patch("src.rl.policy.np.random.choice", return_value="gain_food")
    def test_policy_choose_action(self, mock_choice):
        state = Mock()
        state.phase = "choose_action"
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "gain_food")

    @patch("src.rl.policy.np.random.choice", return_value="Osprey")
    def test_policy_choose_a_bird_to_play(self, mock_choice):
        state = Mock()
        state.phase = "choose_a_bird_to_play"
        actions = ["Osprey", "Cardinal"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "Osprey")

    @patch("src.rl.policy.np.random.choice", return_value="deck")
    def test_policy_choose_a_bird_to_draw(self, mock_choice):
        state = Mock()
        state.phase = "choose_a_bird_to_draw"
        actions = ["Blue Jay", "deck"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "deck")

    def test_call_dispatches_by_phase(self):
        for phase in ["choose_action", "choose_a_bird_to_play", "choose_a_bird_to_draw"]:
            state = Mock()
            state.phase = phase
            actions = ["action1", "action2"]
            result = self.policy(state, actions)
            self.assertIn(result, actions)


if __name__ == "__main__":
    unittest.main()
