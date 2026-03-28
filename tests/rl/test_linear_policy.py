import os
import tempfile
import unittest

import numpy as np

from src.game import WingspanGame
from src.rl.featurizer import NUM_FEATURES
from src.rl.linear_policy import LinearPolicy


class TestLinearPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()
        self.game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        self.state = self.game.game_state

    def test_initial_weights_are_zero(self):
        self.assertTrue(np.all(self.policy.weights == 0))
        self.assertEqual(self.policy.weights.shape, (NUM_FEATURES, 3))

    def test_choose_action_returns_legal(self):
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        self.state.phase = "choose_action"
        result = self.policy(self.state, actions)
        self.assertIn(result, actions)

    def test_choose_action_with_subset(self):
        actions = ["gain_food", "draw_a_bird"]
        self.state.phase = "choose_action"
        result = self.policy(self.state, actions)
        self.assertIn(result, actions)

    def test_get_action_probabilities_sums_to_one(self):
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        probs = self.policy.get_action_probabilities(self.state, actions)
        self.assertAlmostEqual(np.sum(probs), 1.0)

    def test_uniform_with_zero_weights(self):
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        probs = self.policy.get_action_probabilities(self.state, actions)
        np.testing.assert_allclose(probs, [1 / 3, 1 / 3, 1 / 3])

    def test_nonzero_weights_change_distribution(self):
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        self.policy.weights[:, 0] = 10.0  # Heavily favor play_a_bird (column 0)
        probs = self.policy.get_action_probabilities(self.state, actions)
        self.assertGreater(probs[0], probs[1])
        self.assertGreater(probs[0], probs[2])

    def test_canonical_indices_stable_with_subset(self):
        # With all 3 actions, column 1 = gain_food
        self.policy.weights[:, 1] = 10.0
        all_probs = self.policy.get_action_probabilities(self.state, ["play_a_bird", "gain_food", "draw_a_bird"])
        # With 2 actions, gain_food should still map to column 1
        sub_probs = self.policy.get_action_probabilities(self.state, ["gain_food", "draw_a_bird"])
        # gain_food should have highest probability in both cases
        self.assertEqual(np.argmax(all_probs), 1)  # index of gain_food in full list
        self.assertEqual(np.argmax(sub_probs), 0)  # index of gain_food in subset

    def test_save_and_load(self):
        self.policy.weights = np.random.randn(NUM_FEATURES, 3)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "policy.npz")
            self.policy.save(path)
            loaded = LinearPolicy.load(path)
            np.testing.assert_array_equal(loaded.weights, self.policy.weights)

    def test_bird_sub_decision_is_uniform(self):
        self.state.phase = "choose_a_bird_to_play"
        birds = ["Osprey", "Cardinal"]
        self.policy.weights[:, 0] = 100.0  # Should not affect sub-decisions
        probs = self.policy.get_action_probabilities(self.state, birds)
        np.testing.assert_allclose(probs, [0.5, 0.5])

    def test_draw_sub_decision_is_uniform(self):
        self.state.phase = "choose_a_bird_to_draw"
        choices = ["Blue Jay", "Cardinal", "deck"]
        probs = self.policy.get_action_probabilities(self.state, choices)
        np.testing.assert_allclose(probs, [1 / 3, 1 / 3, 1 / 3])


if __name__ == "__main__":
    unittest.main()
