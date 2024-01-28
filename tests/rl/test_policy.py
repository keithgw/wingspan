from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
import unittest
from unittest.mock import Mock, patch
from src.rl.policy import RandomPolicy

class TestRandomPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomPolicy()
        self.mock_state = Mock()

    @patch('numpy.random.choice', return_value='play_a_bird')
    def test_policy_choose_action_three_actions(self, mock_np):
        legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        action = self.policy._policy_choose_action(state=self.mock_state, legal_actions=legal_actions)
        mock_np.assert_called_once_with(legal_actions, p=[1/3, 1/3, 1/3])
        self.assertEqual(action, 'play_a_bird')

    @patch('numpy.random.choice', return_value='play_a_bird')
    def test_policy_choose_action_two_actions(self, mock_np):
        legal_actions = ['play_a_bird', 'gain_food']
        action = self.policy._policy_choose_action(state=self.mock_state, legal_actions=legal_actions)
        mock_np.assert_called_once_with(legal_actions, p=[1/2, 1/2])
        self.assertEqual(action, 'play_a_bird')

    @patch('numpy.random.choice', return_value='bird1')
    def test_policy_choose_a_bird_to_play(self, mock_np):
        playable_birds = ['bird1', 'bird2', 'bird3']
        bird = self.policy._policy_choose_a_bird_to_play(state=self.mock_state, playable_birds=playable_birds)
        mock_np.assert_called_once_with(playable_birds, p=[1/3, 1/3, 1/3])
        self.assertEqual(bird, 'bird1')

    @patch('numpy.random.choice', return_value='deck')
    def test_policy_choose_a_bird_to_draw(self, mock_np):
        valid_choices = ['bird1', 'bird2', 'bird3', 'deck']
        choice = self.policy._policy_choose_a_bird_to_draw(state=self.mock_state, valid_choices=valid_choices)
        mock_np.assert_called_once_with(valid_choices, p=[1/4, 1/4, 1/4, 1/4])
        self.assertEqual(choice, 'deck')

    @patch.object(RandomPolicy, '_policy_choose_action', return_value='play_a_bird')
    def test_call_choose_action(self, mock_policy_choose_action):
        mock_state = Mock()
        mock_state.phase = CHOOSE_ACTION
        legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        action = self.policy(mock_state, legal_actions)
        mock_policy_choose_action.assert_called_once_with(mock_state, legal_actions)
        self.assertEqual(action, 'play_a_bird')

    @patch.object(RandomPolicy, '_policy_choose_a_bird_to_play', return_value='bird1')
    def test_call_choose_a_bird_to_play(self, mock_policy_choose_a_bird_to_play):
        mock_state = Mock()
        mock_state.phase = CHOOSE_A_BIRD_TO_PLAY
        playable_birds = ['bird1', 'bird2', 'bird3']
        bird = self.policy(mock_state, playable_birds)
        mock_policy_choose_a_bird_to_play.assert_called_once_with(mock_state, playable_birds)
        self.assertEqual(bird, 'bird1')

    @patch.object(RandomPolicy, '_policy_choose_a_bird_to_draw', return_value='deck')
    def test_call_choose_a_bird_to_draw(self, mock_policy_choose_a_bird_to_draw):
        mock_state = Mock()
        mock_state.phase = CHOOSE_A_BIRD_TO_DRAW
        valid_choices = ['bird1', 'bird2', 'bird3', 'deck']
        choice = self.policy(mock_state, valid_choices)
        mock_policy_choose_a_bird_to_draw.assert_called_once_with(mock_state, valid_choices)
        self.assertEqual(choice, 'deck')


if __name__ == '__main__':
    unittest.main()