import numpy as np

from src.rl.featurizer import NUM_FEATURES, featurize
from src.rl.policy import Policy


class LinearPolicy(Policy):
    """Policy that selects actions via a linear model over state features.

    Maps featurize(state) @ weights → logits per action, then softmax over
    legal actions. Weights are interpretable: each row is a feature, each
    column is an action preference.
    """

    def __init__(self, num_actions=3):
        self.num_actions = num_actions
        self.weights = np.zeros((NUM_FEATURES, num_actions), dtype=np.float64)

    def _score_actions(self, state, actions):
        """Return (features, probabilities) for the given actions.

        For CHOOSE_ACTION (up to num_actions choices), uses learned weights.
        For other phases (variable action count), defaults to uniform —
        the linear model focuses on the strategic action choice.
        """
        features = featurize(state)
        n = len(actions)

        if n <= self.num_actions:
            logits = (features @ self.weights)[:n]
        else:
            # More actions than weight columns (e.g., 4 tray birds) — uniform
            logits = np.zeros(n)

        # Softmax with numerical stability
        shifted = logits - np.max(logits)
        exp_scores = np.exp(shifted)
        probs = exp_scores / np.sum(exp_scores)

        return features, probs

    def get_action_probabilities(self, state, actions):
        """Return probability distribution over actions (for training)."""
        _, probs = self._score_actions(state, actions)
        return probs

    def _choose(self, state, actions):
        """Score actions and sample one."""
        _, probs = self._score_actions(state, actions)
        return np.random.choice(actions, p=probs)

    def _policy_choose_action(self, state, legal_actions):
        return self._choose(state, legal_actions)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._choose(state, playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._choose(state, valid_choices)

    def save(self, path):
        """Save weights to a .npz file."""
        np.savez(path, weights=self.weights)

    @classmethod
    def load(cls, path):
        """Load a LinearPolicy from a .npz file."""
        data = np.load(path)
        policy = cls(num_actions=data["weights"].shape[1])
        policy.weights = data["weights"]
        return policy
