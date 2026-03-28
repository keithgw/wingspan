import numpy as np

from src.rl.featurizer import (
    ACTION_INDEX,
    NUM_FEATURES,
    NUM_SUB_FEATURES,
    featurize,
    featurize_option,
)
from src.rl.policy import Policy


class LinearPolicy(Policy):
    """Policy with two linear models: one for action choice, one for sub-decisions.

    Action choice: featurize(state) @ weights → logits per action (play/gain/draw).
    Sub-decisions: [state_features; option_features] @ sub_weights → score per option.

    Both are interpretable: weights show which features drive each decision.
    """

    def __init__(self, num_actions=3):
        self.num_actions = num_actions
        self.weights = np.zeros((NUM_FEATURES, num_actions), dtype=np.float64)
        self.sub_weights = np.zeros(NUM_SUB_FEATURES, dtype=np.float64)

    def _score_actions(self, state, actions):
        """Return (features, probabilities) for CHOOSE_ACTION phase."""
        features = featurize(state)
        all_logits = features @ self.weights
        indices = [ACTION_INDEX[a] for a in actions]
        logits = all_logits[indices]

        probs = _softmax(logits)
        return features, probs

    def _score_options(self, state, options):
        """Return (combined_features_list, probabilities) for sub-decisions.

        Each option gets scored by concatenating state features with
        per-option features and dotting with sub_weights.
        """
        state_features = featurize(state)
        combined_list = []
        scores = []

        for option_name in options:
            option_features = featurize_option(state, option_name)
            combined = np.concatenate([state_features, option_features])
            combined_list.append(combined)
            scores.append(combined @ self.sub_weights)

        logits = np.array(scores)
        probs = _softmax(logits)
        return combined_list, probs

    def get_action_probabilities(self, state, actions):
        """Return probability distribution over actions."""
        canonical = all(a in ACTION_INDEX for a in actions)
        if canonical:
            _, probs = self._score_actions(state, actions)
        else:
            _, probs = self._score_options(state, actions)
        return probs

    def _policy_choose_action(self, state, legal_actions):
        _, probs = self._score_actions(state, legal_actions)
        return np.random.choice(legal_actions, p=probs)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        _, probs = self._score_options(state, playable_birds)
        return np.random.choice(playable_birds, p=probs)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        _, probs = self._score_options(state, valid_choices)
        return np.random.choice(valid_choices, p=probs)

    def save(self, path):
        """Save weights to a .npz file."""
        np.savez(path, weights=self.weights, sub_weights=self.sub_weights)

    @classmethod
    def load(cls, path):
        """Load a LinearPolicy from a .npz file."""
        data = np.load(path)
        policy = cls(num_actions=data["weights"].shape[1])
        policy.weights = data["weights"]
        if "sub_weights" in data:
            policy.sub_weights = data["sub_weights"]
        return policy


def _softmax(logits):
    """Numerically stable softmax."""
    shifted = logits - np.max(logits)
    exp_scores = np.exp(shifted)
    return exp_scores / np.sum(exp_scores)
