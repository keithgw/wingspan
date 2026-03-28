"""Self-play infrastructure for collecting training experience."""

import contextlib
import io
from collections import namedtuple

import numpy as np

from src.rl.featurizer import featurize
from src.rl.policy import Policy

Experience = namedtuple("Experience", ["features", "action_index", "reward"])


class LoggingPolicy(Policy):
    """Wraps a policy to log (features, action_index) at each decision.

    After a game, call assign_rewards() to pair each logged decision
    with the game outcome.
    """

    def __init__(self, inner_policy):
        self.inner_policy = inner_policy
        self.log = []  # list of (features, action_index)

    def _log_and_choose(self, state, actions):
        features = featurize(state)
        chosen = self.inner_policy(state, actions)
        action_index = actions.index(chosen)
        self.log.append((features, action_index))
        return chosen

    def _policy_choose_action(self, state, legal_actions):
        return self._log_and_choose(state, legal_actions)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._log_and_choose(state, playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._log_and_choose(state, valid_choices)

    def assign_rewards(self, reward):
        """Convert logged decisions into Experience tuples with the given reward."""
        return [Experience(features=f, action_index=a, reward=reward) for f, a in self.log]

    def clear(self):
        self.log = []


class SelfPlayRunner:
    """Runs bot-vs-bot games and collects training experience."""

    def run_game(self, policy, opponent_policy=None, num_turns=10):
        """Play one game and return experiences for the learning player (player 0).

        Args:
            policy: The policy being trained (plays as player 0).
            opponent_policy: The opponent's policy. Defaults to a copy of policy.
            num_turns: Turns per player.

        Returns:
            Tuple of (experiences, won) where experiences is a list of
            Experience namedtuples and won is 1.0/0.5/0.0.
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

        experiences = logger_0.assign_rewards(reward)
        return experiences, reward

    def collect_experience(self, policy, num_games, opponent_policy=None, num_turns=10):
        """Run N games and return aggregated experiences + stats.

        Returns:
            Tuple of (all_experiences, stats) where stats is a dict with
            'wins', 'losses', 'ties', 'mean_reward'.
        """
        all_experiences = []
        rewards = []

        for _ in range(num_games):
            experiences, reward = self.run_game(policy, opponent_policy=opponent_policy, num_turns=num_turns)
            all_experiences.extend(experiences)
            rewards.append(reward)

        stats = {
            "wins": sum(1 for r in rewards if r == 1.0),
            "losses": sum(1 for r in rewards if r == 0.0),
            "ties": sum(1 for r in rewards if r == 0.5),
            "mean_reward": np.mean(rewards),
        }

        return all_experiences, stats
