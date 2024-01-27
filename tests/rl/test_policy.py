import unittest
from unittest.mock import Mock
from src.rl.policy import RandomPolicy

class TestRandomPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomPolicy()

    def test_policy_choose_action_three_actions(self):
        legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        probabilities = self.policy._policy_choose_action(legal_actions)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_policy_choose_action_two_actions(self):
        legal_actions = ['play_a_bird', 'gain_food']
        probabilities = self.policy._policy_choose_action(legal_actions)
        self.assertEqual(probabilities, [1/2, 1/2])

    def test_policy_choose_a_bird_to_play(self):
        mock_hand = Mock()
        mock_hand.get_cards_in_hand.return_value = ['bird1', 'bird2', 'bird3']
        mock_food_supply = Mock()
        mock_food_supply.can_play_bird.side_effect = [True, False, True]
        probabilities = self.policy._policy_choose_a_bird_to_play(mock_hand, mock_food_supply)
        self.assertEqual(probabilities, [0.5, 0, 0.5])

    def test_policy_choose_a_bird_to_draw_deck_empty(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_deck = Mock()
        mock_deck.get_count.return_value = 0
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3, 0])

    def test_policy_choose_a_bird_to_draw_deck_not_empty(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_deck = Mock()
        mock_deck.get_count.return_value = 1
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/4, 1/4, 1/4, 1/4])

    def test_policy_choose_a_bird_to_draw_tray_partially_filled(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 2
        mock_deck = Mock()
        mock_deck.get_count.return_value = 1
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_call_choose_action(self):
        mock_state = Mock()
        mock_state.phase = 'choose_action'
        mock_state.legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_call_choose_a_bird_to_play(self):
        mock_state = Mock()
        mock_state.phase = 'choose_a_bird_to_play'
        mock_state.bird_hand = Mock()
        mock_state.bird_hand.get_cards_in_hand.return_value = ['bird1', 'bird2', 'bird3']
        mock_state.food_supply = Mock()
        mock_state.food_supply.can_play_bird.side_effect = [True, False, True]
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [0.5, 0, 0.5])

    def test_call_choose_a_bird_to_draw(self):
        mock_state = Mock()
        mock_state.phase = 'choose_a_bird_to_draw'
        mock_state.tray = Mock()
        mock_state.tray.get_count.return_value = 3
        mock_state.bird_deck = Mock()
        mock_state.bird_deck.get_count.return_value = 1
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [1/4, 1/4, 1/4, 1/4])

if __name__ == '__main__':
    unittest.main()