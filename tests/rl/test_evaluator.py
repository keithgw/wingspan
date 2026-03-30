import unittest

from src.rl.evaluator import evaluate, evaluate_parallel
from src.rl.linear_policy import LinearPolicy
from src.rl.policy import RandomPolicy


class TestEvaluate(unittest.TestCase):
    def test_returns_expected_keys(self):
        results = evaluate(RandomPolicy(), RandomPolicy(), num_games=4, num_turns=2)
        expected = {"win_rate", "tie_rate", "mean_score", "mean_opponent_score", "mean_score_diff"}
        self.assertEqual(set(results.keys()), expected)

    def test_win_rate_bounded(self):
        results = evaluate(RandomPolicy(), RandomPolicy(), num_games=4, num_turns=2)
        self.assertGreaterEqual(results["win_rate"], 0.0)
        self.assertLessEqual(results["win_rate"], 1.0)


class TestEvaluateParallel(unittest.TestCase):
    def test_returns_expected_keys(self):
        from concurrent.futures import ProcessPoolExecutor

        policy = LinearPolicy()
        with ProcessPoolExecutor(max_workers=2) as pool:
            results = evaluate_parallel(policy, num_games=4, num_turns=2, pool=pool)
        expected = {"win_rate", "tie_rate", "mean_score", "mean_opponent_score", "mean_score_diff"}
        self.assertEqual(set(results.keys()), expected)

    def test_game_count_matches(self):
        from concurrent.futures import ProcessPoolExecutor

        policy = LinearPolicy()
        with ProcessPoolExecutor(max_workers=2) as pool:
            results = evaluate_parallel(policy, num_games=6, num_turns=2, pool=pool)
        # win_rate + loss_rate + tie_rate should sum to ~1.0
        self.assertAlmostEqual(
            results["win_rate"] + results["tie_rate"] + (1 - results["win_rate"] - results["tie_rate"]), 1.0
        )


if __name__ == "__main__":
    unittest.main()
