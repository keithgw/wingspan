import unittest

import numpy as np

from src.rl.featurizer import NUM_FEATURES, NUM_SUB_FEATURES
from src.rl.linear_policy import LinearPolicy
from src.rl.self_play import ActionExperience, SubExperience
from src.rl.trainer import compute_action_gradient, compute_sub_gradient, train_batch


class TestComputeActionGradient(unittest.TestCase):
    def test_returns_correct_shape(self):
        features = np.random.randn(NUM_FEATURES)
        exp = ActionExperience(features=features, action_index=0, reward=1.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_action_gradient(exp, weights, num_actions=3)
        self.assertEqual(grad.shape, (NUM_FEATURES, 3))

    def test_zero_advantage_gives_zero_gradient(self):
        features = np.random.randn(NUM_FEATURES)
        exp = ActionExperience(features=features, action_index=1, reward=0.5)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_action_gradient(exp, weights, num_actions=3, baseline=0.5)
        np.testing.assert_array_almost_equal(grad, np.zeros_like(grad))

    def test_positive_advantage_reinforces_action(self):
        features = np.ones(NUM_FEATURES)
        exp = ActionExperience(features=features, action_index=0, reward=1.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_action_gradient(exp, weights, num_actions=3, baseline=0.5)
        self.assertGreater(np.sum(grad[:, 0]), 0)

    def test_negative_advantage_discourages_action(self):
        features = np.ones(NUM_FEATURES)
        exp = ActionExperience(features=features, action_index=0, reward=0.0)
        weights = np.zeros((NUM_FEATURES, 3))
        grad = compute_action_gradient(exp, weights, num_actions=3, baseline=0.5)
        self.assertLess(np.sum(grad[:, 0]), 0)


class TestComputeSubGradient(unittest.TestCase):
    def test_returns_correct_shape(self):
        combined = np.random.randn(NUM_SUB_FEATURES)
        exp = SubExperience(combined_features=combined, action_index=0, num_options=3, reward=1.0)
        sub_weights = np.zeros(NUM_SUB_FEATURES)
        grad = compute_sub_gradient(exp, sub_weights, baseline=0.5)
        self.assertEqual(grad.shape, (NUM_SUB_FEATURES,))

    def test_zero_advantage_gives_zero_gradient(self):
        combined = np.random.randn(NUM_SUB_FEATURES)
        exp = SubExperience(combined_features=combined, action_index=0, num_options=2, reward=0.5)
        sub_weights = np.zeros(NUM_SUB_FEATURES)
        grad = compute_sub_gradient(exp, sub_weights, baseline=0.5)
        np.testing.assert_array_almost_equal(grad, np.zeros_like(grad))


class TestTrainBatch(unittest.TestCase):
    def test_updates_action_weights(self):
        policy = LinearPolicy()
        features = np.random.randn(NUM_FEATURES)
        action_exps = [
            ActionExperience(features=features, action_index=0, reward=1.0),
            ActionExperience(features=features, action_index=1, reward=0.0),
        ]
        weights_before = policy.weights.copy()
        train_batch(policy, action_exps, [], learning_rate=0.1)
        self.assertFalse(np.array_equal(policy.weights, weights_before))

    def test_updates_sub_weights(self):
        policy = LinearPolicy()
        feat_a = np.random.randn(NUM_SUB_FEATURES)
        feat_b = np.random.randn(NUM_SUB_FEATURES)
        sub_exps = [
            SubExperience(combined_features=feat_a, action_index=0, num_options=3, reward=1.0),
            SubExperience(combined_features=feat_b, action_index=1, num_options=3, reward=0.0),
        ]
        sub_before = policy.sub_weights.copy()
        train_batch(policy, [], sub_exps, learning_rate=0.1)
        self.assertFalse(np.array_equal(policy.sub_weights, sub_before))

    def test_empty_experiences_returns_zero(self):
        policy = LinearPolicy()
        result = train_batch(policy, [], [], learning_rate=0.1)
        self.assertEqual(result, 0.0)

    def test_returns_baseline(self):
        policy = LinearPolicy()
        features = np.random.randn(NUM_FEATURES)
        action_exps = [
            ActionExperience(features=features, action_index=0, reward=1.0),
            ActionExperience(features=features, action_index=1, reward=0.0),
        ]
        baseline = train_batch(policy, action_exps, [], learning_rate=0.01)
        self.assertAlmostEqual(baseline, 0.5)


if __name__ == "__main__":
    unittest.main()
