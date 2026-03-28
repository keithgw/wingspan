"""REINFORCE training for LinearPolicy."""

import numpy as np


def compute_policy_gradient(experience, weights, num_actions, baseline=0.0):
    """Compute the REINFORCE gradient for a single experience.

    grad_log_pi = features^T * (one_hot(action) - softmax(logits)) * (reward - baseline)

    The baseline reduces variance: losses (reward < baseline) produce
    negative gradients that discourage the chosen action.
    """
    features = experience.features
    logits = features @ weights[:, :num_actions]

    # Softmax
    shifted = logits - np.max(logits)
    exp_logits = np.exp(shifted)
    probs = exp_logits / np.sum(exp_logits)

    # One-hot for the taken action
    one_hot = np.zeros(num_actions)
    one_hot[experience.action_index] = 1.0

    # Advantage = reward - baseline
    advantage = experience.reward - baseline
    grad = np.outer(features, (one_hot - probs)) * advantage
    return grad


def train_batch(policy, experiences, learning_rate=0.01):
    """Update policy weights using REINFORCE with baseline on a batch of experiences.

    Uses mean batch reward as the baseline so that losses produce negative
    gradients and the policy learns from both wins and losses.

    Returns the mean reward of the batch (for monitoring).
    """
    if not experiences:
        return 0.0

    num_actions = policy.num_actions
    baseline = np.mean([exp.reward for exp in experiences])

    total_grad = np.zeros_like(policy.weights)

    for exp in experiences:
        grad = compute_policy_gradient(exp, policy.weights, num_actions, baseline=baseline)
        total_grad[:, :num_actions] += grad

    # Average gradient and apply
    policy.weights += learning_rate * total_grad / len(experiences)

    return baseline
