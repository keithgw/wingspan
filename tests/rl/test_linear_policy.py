import os
import tempfile
import unittest

import numpy as np

from src.game import WingspanGame
from src.rl.featurizer import NUM_FEATURES, NUM_SUB_FEATURES
from src.rl.linear_policy import LinearPolicy


class TestLinearPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()
        self.game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        self.state = self.game.game_state

    def test_initial_weights_are_zero(self):
        self.assertTrue(np.all(self.policy.weights == 0))
        self.assertEqual(self.policy.weights.shape, (NUM_FEATURES, 3))
        self.assertTrue(np.all(self.policy.sub_weights == 0))
        self.assertEqual(self.policy.sub_weights.shape, (NUM_SUB_FEATURES,))

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
        self.policy.weights[:, 0] = 10.0
        probs = self.policy.get_action_probabilities(self.state, actions)
        self.assertGreater(probs[0], probs[1])
        self.assertGreater(probs[0], probs[2])

    def test_canonical_indices_stable_with_subset(self):
        self.policy.weights[:, 1] = 10.0
        all_probs = self.policy.get_action_probabilities(self.state, ["play_a_bird", "gain_food", "draw_a_bird"])
        sub_probs = self.policy.get_action_probabilities(self.state, ["gain_food", "draw_a_bird"])
        self.assertEqual(np.argmax(all_probs), 1)
        self.assertEqual(np.argmax(sub_probs), 0)

    def test_save_and_load(self):
        self.policy.weights = np.random.randn(NUM_FEATURES, 3)
        self.policy.sub_weights = np.random.randn(NUM_SUB_FEATURES)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "policy.npz")
            self.policy.save(path)
            loaded = LinearPolicy.load(path)
            np.testing.assert_array_equal(loaded.weights, self.policy.weights)
            np.testing.assert_array_equal(loaded.sub_weights, self.policy.sub_weights)

    def test_load_backwards_compatible(self):
        """Loading a policy saved without sub_weights gets zero sub_weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "old_policy.npz")
            np.savez(path, weights=np.random.randn(NUM_FEATURES, 3))
            loaded = LinearPolicy.load(path)
            self.assertTrue(np.all(loaded.sub_weights == 0))

    def test_sub_decision_bird_to_play(self):
        self.state.phase = "choose_a_bird_to_play"
        hand_birds = self.state.get_current_player().get_bird_hand().get_cards_in_hand()
        bird_names = [b.get_name() for b in hand_birds]
        result = self.policy(self.state, bird_names)
        self.assertIn(result, bird_names)

    def test_sub_decision_bird_to_draw(self):
        self.state.phase = "choose_a_bird_to_draw"
        tray_names = self.state.get_tray().see_birds_in_tray()
        choices = tray_names + ["deck"]
        result = self.policy(self.state, choices)
        self.assertIn(result, choices)

    def test_sub_decision_probabilities_sum_to_one(self):
        self.state.phase = "choose_a_bird_to_draw"
        choices = self.state.get_tray().see_birds_in_tray() + ["deck"]
        probs = self.policy.get_action_probabilities(self.state, choices)
        self.assertAlmostEqual(np.sum(probs), 1.0)

    def test_sub_weights_affect_distribution(self):
        self.state.phase = "choose_a_bird_to_draw"
        choices = self.state.get_tray().see_birds_in_tray() + ["deck"]
        probs_before = self.policy.get_action_probabilities(self.state, choices)
        self.policy.sub_weights[NUM_FEATURES] = 50.0  # option_points feature
        probs_after = self.policy.get_action_probabilities(self.state, choices)
        self.assertFalse(np.allclose(probs_before, probs_after))


if __name__ == "__main__":
    unittest.main()
