import unittest

from src.rl.featurizer import ACTION_INDEX, NUM_FEATURES, NUM_SUB_FEATURES
from src.rl.linear_policy import LinearPolicy
from src.rl.policy import RandomPolicy
from src.rl.self_play import ActionExperience, LoggingPolicy, SelfPlayRunner, SubExperience


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
        self.assertEqual(len(self.logger.action_log), 1)
        features, action_index = self.logger.action_log[0]
        self.assertEqual(features.shape, (NUM_FEATURES,))
        self.assertEqual(action_index, ACTION_INDEX[result])

    def test_logs_sub_decisions(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_a_bird_to_draw"
        tray_names = state.get_tray().see_birds_in_tray()
        choices = tray_names + ["deck"]
        self.logger(state, choices)
        self.assertEqual(len(self.logger.sub_log), 1)
        combined_list, chosen_idx = self.logger.sub_log[0]
        self.assertEqual(len(combined_list), len(choices))
        self.assertEqual(combined_list[0].shape, (NUM_SUB_FEATURES,))

    def test_assign_rewards_separates_types(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state

        state.phase = "choose_action"
        self.logger(state, ["gain_food", "draw_a_bird"])

        state.phase = "choose_a_bird_to_draw"
        choices = state.get_tray().see_birds_in_tray() + ["deck"]
        self.logger(state, choices)

        action_exps, sub_exps = self.logger.assign_rewards(1.0)
        self.assertEqual(len(action_exps), 1)
        self.assertIsInstance(action_exps[0], ActionExperience)
        self.assertEqual(len(sub_exps), 1)
        self.assertIsInstance(sub_exps[0], SubExperience)

    def test_clear(self):
        from src.game import WingspanGame

        game = WingspanGame(num_players=2, num_turns=1, num_starting_cards=2)
        state = game.game_state
        state.phase = "choose_action"
        self.logger(state, ["gain_food"])
        self.logger.clear()
        self.assertEqual(len(self.logger.action_log), 0)
        self.assertEqual(len(self.logger.sub_log), 0)


class TestSelfPlayRunner(unittest.TestCase):
    def setUp(self):
        self.runner = SelfPlayRunner()
        self.policy = RandomPolicy()

    def test_run_game_returns_both_experience_types(self):
        action_exps, sub_exps, reward = self.runner.run_game(self.policy, num_turns=2)
        self.assertGreater(len(action_exps), 0)
        self.assertIn(reward, (0.0, 0.5, 1.0))
        # Sub experiences may or may not exist depending on actions chosen
        for exp in action_exps:
            self.assertEqual(exp.features.shape, (NUM_FEATURES,))
            self.assertIn(exp.action_index, (0, 1, 2))

    def test_run_game_with_different_opponent(self):
        opponent = LinearPolicy()
        action_exps, sub_exps, reward = self.runner.run_game(self.policy, opponent_policy=opponent, num_turns=2)
        self.assertGreater(len(action_exps), 0)

    def test_collect_experience(self):
        action_exps, sub_exps, stats = self.runner.collect_experience(self.policy, num_games=5, num_turns=2)
        self.assertGreater(len(action_exps), 0)
        self.assertEqual(stats["wins"] + stats["losses"] + stats["ties"], 5)


if __name__ == "__main__":
    unittest.main()
