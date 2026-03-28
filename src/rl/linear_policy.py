import numpy as np

from src.rl.featurizer import ACTION_INDEX, NUM_FEATURES, featurize
from src.rl.policy import Policy


class LinearPolicy(Policy):
    """Policy that selects actions via a linear model over state features.

    Maps featurize(state) @ weights → logits per action, then softmax over
    legal actions. Weights are interpretable: each row is a feature, each
    column is an action preference (play_a_bird=0, gain_food=1, draw_a_bird=2).
    """

    def __init__(self, num_actions=3):
        self.num_actions = num_actions
        self.weights = np.zeros((NUM_FEATURES, num_actions), dtype=np.float64)

    def _score_actions(self, state, actions):
        """Return (features, probabilities) for the given actions.

        For CHOOSE_ACTION phase, maps actions to canonical column indices
        so weights have stable meaning. For other phases (bird/draw
        sub-decisions), defaults to uniform.
        """
        features = featurize(state)

        # Check if all actions have canonical indices
        canonical = all(a in ACTION_INDEX for a in actions)

        if canonical:
            all_logits = features @ self.weights
            indices = [ACTION_INDEX[a] for a in actions]
            logits = all_logits[indices]
        else:
            # Sub-decision (which bird to play/draw) — uniform
            logits = np.zeros(len(actions))

        # Softmax with numerical stability
        shifted = logits - np.max(logits)
        exp_scores = np.exp(shifted)
        probs = exp_scores / np.sum(exp_scores)

        return features, probs

    def get_action_probabilities(self, state, actions):
        """Return probability distribution over actions."""
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
