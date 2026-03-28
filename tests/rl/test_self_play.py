import unittest

from src.rl.featurizer import ACTION_INDEX, NUM_FEATURES
from src.rl.linear_policy import LinearPolicy
from src.rl.policy import RandomPolicy
from src.rl.self_play import Experience, LoggingPolicy, SelfPlayRunner


class TestLoggingPolicy(unittest.TestCase):
    def setUp(self):
        self.inner = RandomPolicy()
        self.logger = LoggingPolicy(self.inner)

    def test_logs_choose_action_decisions(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_action"
        actions = ["gain_food", "draw_a_bird"]
        result = self.logger(state, actions)
        self.assertIn(result, actions)
        self.assertEqual(len(self.logger.log), 1)
        features, action_index = self.logger.log[0]
        self.assertEqual(features.shape, (NUM_FEATURES,))
        self.assertEqual(action_index, ACTION_INDEX[result])

    def test_does_not_log_bird_sub_decisions(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_a_bird_to_play"
        self.logger(state, ["Osprey", "Cardinal"])
        self.assertEqual(len(self.logger.log), 0)

    def test_assign_rewards(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_action"
        self.logger(state, ["gain_food", "draw_a_bird"])
        experiences = self.logger.assign_rewards(1.0)
        self.assertEqual(len(experiences), 1)
        self.assertIsInstance(experiences[0], Experience)
        self.assertEqual(experiences[0].reward, 1.0)

    def test_clear(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_action"
        self.logger(state, ["gain_food"])
        self.logger.clear()
        self.assertEqual(len(self.logger.log), 0)


class TestSelfPlayRunner(unittest.TestCase):
    def setUp(self):
        self.runner = SelfPlayRunner()
        self.policy = RandomPolicy()

    def test_run_game_returns_experiences(self):
        experiences, reward = self.runner.run_game(self.policy, num_turns=2)
        self.assertGreater(len(experiences), 0)
        self.assertIn(reward, (0.0, 0.5, 1.0))

    def test_experiences_have_correct_shape(self):
        experiences, _ = self.runner.run_game(self.policy, num_turns=2)
        for exp in experiences:
            self.assertEqual(exp.features.shape, (NUM_FEATURES,))
            self.assertIsInstance(exp.action_index, int)
            self.assertIn(exp.action_index, (0, 1, 2))
            self.assertIn(exp.reward, (0.0, 0.5, 1.0))

    def test_run_game_with_different_opponent(self):
        opponent = LinearPolicy()
        experiences, reward = self.runner.run_game(self.policy, opponent_policy=opponent, num_turns=2)
        self.assertGreater(len(experiences), 0)

    def test_collect_experience(self):
        all_exp, stats = self.runner.collect_experience(self.policy, num_games=5, num_turns=2)
        self.assertGreater(len(all_exp), 0)
        self.assertEqual(stats["wins"] + stats["losses"] + stats["ties"], 5)
        self.assertGreaterEqual(stats["mean_reward"], 0.0)
        self.assertLessEqual(stats["mean_reward"], 1.0)


if __name__ == "__main__":
    unittest.main()
