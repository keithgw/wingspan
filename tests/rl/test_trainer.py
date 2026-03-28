import unittest

import numpy as np

from src.rl.featurizer import NUM_FEATURES
from src.rl.linear_policy import LinearPolicy
from src.rl.self_play import Experience
from src.rl.trainer import compute_policy_gradient, train_batch


class TestComputePolicyGradient(unittest.TestCase):
    def test_returns_correct_shape(self):
        features = np.random.randn(NUM_FEATURES)
        exp = Experience(features=features, action_index=0, reward=1.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_policy_gradient(exp, weights, num_actions=3)
        self.assertEqual(grad.shape, (NUM_FEATURES, 3))

    def test_zero_advantage_gives_zero_gradient(self):
        features = np.random.randn(NUM_FEATURES)
        exp = Experience(features=features, action_index=1, reward=0.5)
        weights = np.zeros((NUM_FEATURES, 3))
        # baseline = reward → advantage = 0
        grad = compute_policy_gradient(exp, weights, num_actions=3, baseline=0.5)
        np.testing.assert_array_almost_equal(grad, np.zeros_like(grad))

    def test_positive_advantage_reinforces_action(self):
        features = np.ones(NUM_FEATURES)
        exp = Experience(features=features, action_index=0, reward=1.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_policy_gradient(exp, weights, num_actions=3, baseline=0.5)
        # Gradient for the chosen action column should be positive
        self.assertGreater(np.sum(grad[:, 0]), 0)

    def test_negative_advantage_discourages_action(self):
        features = np.ones(NUM_FEATURES)
        exp = Experience(features=features, action_index=0, reward=0.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_policy_gradient(exp, weights, num_actions=3, baseline=0.5)
        # Gradient for the chosen action column should be negative
        self.assertLess(np.sum(grad[:, 0]), 0)


class TestTrainBatch(unittest.TestCase):
    def test_updates_weights(self):
        policy = LinearPolicy()
        features = np.random.randn(NUM_FEATURES)
        # Mix of wins and losses so baseline doesn't zero everything
        experiences = [
            Experience(features=features, action_index=0, reward=1.0),
            Experience(features=features, action_index=1, reward=0.0),
        ]
        weights_before = policy.weights.copy()
        train_batch(policy, experiences, learning_rate=0.1)
        self.assertFalse(np.array_equal(policy.weights, weights_before))

    def test_empty_experiences_returns_zero(self):
        policy = LinearPolicy()
        result = train_batch(policy, [], learning_rate=0.1)
        self.assertEqual(result, 0.0)

    def test_returns_baseline(self):
        policy = LinearPolicy()
        features = np.random.randn(NUM_FEATURES)
        experiences = [
            Experience(features=features, action_index=0, reward=1.0),
            Experience(features=features, action_index=1, reward=0.0),
        ]
        baseline = train_batch(policy, experiences, learning_rate=0.01)
        self.assertAlmostEqual(baseline, 0.5)

    def test_all_same_reward_no_weight_change(self):
        policy = LinearPolicy()
        features = np.random.randn(NUM_FEATURES)
        # All same reward → advantage = 0 for everyone → no gradient
        experiences = [
            Experience(features=features, action_index=0, reward=1.0),
            Experience(features=features, action_index=1, reward=1.0),
        ]
        weights_before = policy.weights.copy()
        train_batch(policy, experiences, learning_rate=0.1)
        np.testing.assert_array_almost_equal(policy.weights, weights_before)


if __name__ == "__main__":
    unittest.main()
