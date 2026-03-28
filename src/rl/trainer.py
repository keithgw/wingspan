"""REINFORCE training for LinearPolicy."""

import numpy as np

from src.rl.linear_policy import _softmax


def compute_action_gradient(experience, weights, num_actions, baseline=0.0):
    """Compute REINFORCE gradient for an action-level experience.

    Updates the action weights matrix.
    """
    features = experience.features
    logits = features @ weights[:, :num_actions]
    probs = _softmax(logits)

    one_hot = np.zeros(num_actions)
    one_hot[experience.action_index] = 1.0

    advantage = experience.reward - baseline
    return np.outer(features, (one_hot - probs)) * advantage


def compute_sub_gradient(experience, sub_weights, baseline=0.0):
    """Compute REINFORCE gradient for a sub-decision experience.

    The sub-decision uses a single weight vector. The gradient of
    log_softmax w.r.t. the weight vector for the chosen option is:
    combined_features * (1 - prob_chosen) * advantage
    (simplified from the full softmax gradient for the chosen action).
    """
    combined = experience.combined_features
    advantage = experience.reward - baseline
    return combined * advantage


def train_batch(policy, action_experiences, sub_experiences, learning_rate=0.01):
    """Update policy weights using REINFORCE with baseline.

    Updates both action weights and sub-decision weights.
    Returns the mean reward (for monitoring).
    """
    all_rewards = [e.reward for e in action_experiences] + [e.reward for e in sub_experiences]
    if not all_rewards:
        return 0.0

    baseline = np.mean(all_rewards)

    # Update action weights
    if action_experiences:
        num_actions = policy.num_actions
        action_grad = np.zeros_like(policy.weights)
        for exp in action_experiences:
            action_grad[:, :num_actions] += compute_action_gradient(exp, policy.weights, num_actions, baseline=baseline)
        policy.weights += learning_rate * action_grad / len(action_experiences)

    # Update sub-decision weights
    if sub_experiences:
        sub_grad = np.zeros_like(policy.sub_weights)
        for exp in sub_experiences:
            sub_grad += compute_sub_gradient(exp, policy.sub_weights, baseline=baseline)
        policy.sub_weights += learning_rate * sub_grad / len(sub_experiences)

    return baseline
