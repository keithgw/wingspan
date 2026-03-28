"""REINFORCE training for LinearPolicy."""

import numpy as np


def compute_policy_gradient(experience, weights, num_actions):
    """Compute the REINFORCE gradient for a single experience.

    grad_log_pi = features * (one_hot(action) - softmax(logits))
    scaled by reward.
    """
    features = experience.features
    logits = features @ weights[:, :num_actions]

    # Softmax
    shifted = logits - np.max(logits)
    exp_logits = np.exp(shifted)
    probs = exp_logits / np.sum(exp_logits)

    # One-hot for the taken action
    one_hot = np.zeros(num_actions)
    action_idx = min(experience.action_index, num_actions - 1)
    one_hot[action_idx] = 1.0

    # grad_log_pi = features^T * (one_hot - probs), scaled by reward
    grad = np.outer(features, (one_hot - probs)) * experience.reward
    return grad


def train_batch(policy, experiences, learning_rate=0.01):
    """Update policy weights using REINFORCE on a batch of experiences.

    Returns the mean reward of the batch (for monitoring).
    """
    if not experiences:
        return 0.0

    num_actions = policy.num_actions
    total_grad = np.zeros_like(policy.weights)

    for exp in experiences:
        grad = compute_policy_gradient(exp, policy.weights, num_actions)
        # Pad gradient columns if fewer actions than policy columns
        total_grad[:, :num_actions] += grad

    # Average gradient and apply
    policy.weights += learning_rate * total_grad / len(experiences)

    return np.mean([exp.reward for exp in experiences])
