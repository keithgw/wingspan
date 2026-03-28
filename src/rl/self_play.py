"""Self-play infrastructure for collecting training experience."""

import contextlib
import io
from collections import namedtuple

import numpy as np

from src.rl.featurizer import ACTION_INDEX, featurize, featurize_option
from src.rl.policy import Policy

# Action-level experience (CHOOSE_ACTION phase)
ActionExperience = namedtuple("ActionExperience", ["features", "action_index", "reward"])

# Sub-decision experience (which bird to play/draw)
SubExperience = namedtuple("SubExperience", ["combined_features", "action_index", "num_options", "reward"])


class LoggingPolicy(Policy):
    """Wraps a policy to log decisions for training.

    Logs action-level choices (CHOOSE_ACTION) and sub-decisions
    (which bird to play/draw) separately, since they use different
    weight vectors.
    """

    def __init__(self, inner_policy):
        self.inner_policy = inner_policy
        self.action_log = []  # (features, canonical_action_index)
        self.sub_log = []  # (combined_features_list, chosen_index)

    def _policy_choose_action(self, state, legal_actions):
        features = featurize(state)
        chosen = self.inner_policy(state, legal_actions)
        self.action_log.append((features, ACTION_INDEX[chosen]))
        return chosen

    def _log_sub_decision(self, state, options):
        """Log a sub-decision and return the chosen option."""
        chosen = self.inner_policy(state, options)
        chosen_index = options.index(chosen)

        # Build combined features for each option
        state_features = featurize(state)
        combined_list = []
        for option_name in options:
            option_features = featurize_option(state, option_name)
            combined_list.append(np.concatenate([state_features, option_features]))

        self.sub_log.append((combined_list, chosen_index))
        return chosen

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._log_sub_decision(state, playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._log_sub_decision(state, valid_choices)

    def assign_rewards(self, reward):
        """Convert logged decisions into experience tuples."""
        action_exps = [ActionExperience(features=f, action_index=a, reward=reward) for f, a in self.action_log]
        sub_exps = [
            SubExperience(
                combined_features=combined_list[chosen_idx],
                action_index=chosen_idx,
                num_options=len(combined_list),
                reward=reward,
            )
            for combined_list, chosen_idx in self.sub_log
        ]
        return action_exps, sub_exps

    def clear(self):
        self.action_log = []
        self.sub_log = []


class SelfPlayRunner:
    """Runs bot-vs-bot games and collects training experience."""

    def run_game(self, policy, opponent_policy=None, num_turns=10):
        """Play one game and return experiences for the learning player (player 0).

        Returns:
            Tuple of (action_experiences, sub_experiences, reward).
        """
        from src.game import WingspanGame

        if opponent_policy is None:
            opponent_policy = policy

        logger_0 = LoggingPolicy(policy)
        logger_1 = LoggingPolicy(opponent_policy)
        policies = [logger_0, logger_1]
        call_count = [0]

        def policy_factory():
            idx = call_count[0]
            call_count[0] += 1
            return policies[idx]

        with contextlib.redirect_stdout(io.StringIO()):
            game = WingspanGame(
                num_players=2,
                num_human=0,
                num_turns=num_turns,
                bot_policy_factory=policy_factory,
            )
            game.play()

        scores = game.get_player_scores()
        if scores[0] > scores[1]:
            reward = 1.0
        elif scores[0] < scores[1]:
            reward = 0.0
        else:
            reward = 0.5

        action_exps, sub_exps = logger_0.assign_rewards(reward)
        return action_exps, sub_exps, reward

    def collect_experience(self, policy, num_games, opponent_policy=None, num_turns=10):
        """Run N games and return aggregated experiences + stats.

        Returns:
            Tuple of (action_experiences, sub_experiences, stats).
        """
        all_action_exps = []
        all_sub_exps = []
        rewards = []

        for _ in range(num_games):
            action_exps, sub_exps, reward = self.run_game(policy, opponent_policy=opponent_policy, num_turns=num_turns)
            all_action_exps.extend(action_exps)
            all_sub_exps.extend(sub_exps)
            rewards.append(reward)

        stats = {
            "wins": sum(1 for r in rewards if r == 1.0),
            "losses": sum(1 for r in rewards if r == 0.0),
            "ties": sum(1 for r in rewards if r == 0.5),
            "mean_reward": np.mean(rewards),
        }

        return all_action_exps, all_sub_exps, stats
