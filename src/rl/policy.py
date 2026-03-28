import numpy as np

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY, CHOOSE_ACTION


class Policy:
    def __call__(self, state, actions):
        if state.phase == CHOOSE_ACTION:
            return self._policy_choose_action(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_PLAY:
            return self._policy_choose_a_bird_to_play(state, actions)
        elif state.phase == CHOOSE_A_BIRD_TO_DRAW:
            return self._policy_choose_a_bird_to_draw(state, actions)

    def _policy_choose_action(self, state, legal_actions):
        raise NotImplementedError

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        raise NotImplementedError

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        raise NotImplementedError


class RandomPolicy(Policy):
    def _uniform_random_choice(self, actions):
        """Return a choice uniformly at random from the list of actions."""
        return np.random.choice(actions)

    def _policy_choose_action(self, state, legal_actions):
        return self._uniform_random_choice(legal_actions)

    def _policy_choose_a_bird_to_play(self, state, playable_birds):
        return self._uniform_random_choice(playable_birds)

    def _policy_choose_a_bird_to_draw(self, state, valid_choices):
        return self._uniform_random_choice(valid_choices)
