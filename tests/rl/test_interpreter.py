import os
import tempfile
import unittest

import numpy as np

from src.game import WingspanGame
from src.rl.featurizer import ACTION_INDEX, FEATURE_NAMES, NUM_FEATURES, NUM_SUB_FEATURES, OPTION_FEATURE_NAMES
from src.rl.interpreter import (
    StrategyRule,
    compute_feature_importance,
    compute_sub_feature_importance,
    compute_weight_evolution,
    create_sample_states,
    format_strategy_summary,
    generate_strategy_rules,
    get_action_weight_table,
    get_sub_weight_table,
    load_checkpoint_weights,
    rank_features_by_action,
    trace_action_decision,
    trace_sub_decision,
)
from src.rl.linear_policy import LinearPolicy


class TestWeightInspection(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()
        self.policy.weights = np.random.RandomState(0).randn(NUM_FEATURES, 3)
        self.policy.sub_weights = np.random.RandomState(1).randn(NUM_SUB_FEATURES)

    def test_action_weight_table_has_all_features(self):
        table = get_action_weight_table(self.policy)
        self.assertEqual(len(table), NUM_FEATURES)
        for row in table:
            self.assertIn("feature", row)
            self.assertIn("play_a_bird", row)
            self.assertIn("gain_food", row)
            self.assertIn("draw_a_bird", row)

    def test_action_weight_table_values_match(self):
        table = get_action_weight_table(self.policy)
        for i, row in enumerate(table):
            self.assertEqual(row["feature"], FEATURE_NAMES[i])
            self.assertAlmostEqual(row["play_a_bird"], self.policy.weights[i, 0])
            self.assertAlmostEqual(row["gain_food"], self.policy.weights[i, 1])
            self.assertAlmostEqual(row["draw_a_bird"], self.policy.weights[i, 2])

    def test_sub_weight_table_has_all_features(self):
        table = get_sub_weight_table(self.policy)
        self.assertEqual(len(table), NUM_SUB_FEATURES)
        all_names = FEATURE_NAMES + OPTION_FEATURE_NAMES
        for i, row in enumerate(table):
            self.assertEqual(row["feature"], all_names[i])
            self.assertAlmostEqual(row["weight"], self.policy.sub_weights[i])

    def test_rank_features_sorted_by_magnitude(self):
        ranked = rank_features_by_action(self.policy, "play_a_bird")
        self.assertEqual(len(ranked), NUM_FEATURES)
        magnitudes = [abs(w) for _, w in ranked]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))

    def test_rank_features_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            rank_features_by_action(self.policy, "lay_eggs")

    def test_rank_features_all_feature_names_present(self):
        ranked = rank_features_by_action(self.policy, "gain_food")
        names = {name for name, _ in ranked}
        self.assertEqual(names, set(FEATURE_NAMES))


class TestFeatureImportance(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()

    def test_zero_weights_give_zero_importance(self):
        importance = compute_feature_importance(self.policy)
        for _, imp in importance:
            self.assertAlmostEqual(imp, 0.0)

    def test_importance_sums_absolute_weights(self):
        self.policy.weights[0, :] = [1.0, -2.0, 0.5]
        importance = compute_feature_importance(self.policy)
        importance_dict = dict(importance)
        self.assertAlmostEqual(importance_dict[FEATURE_NAMES[0]], 3.5)

    def test_importance_sorted_descending(self):
        self.policy.weights = np.random.RandomState(0).randn(NUM_FEATURES, 3)
        importance = compute_feature_importance(self.policy)
        values = [v for _, v in importance]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_sub_feature_importance_sorted(self):
        self.policy.sub_weights = np.random.RandomState(0).randn(NUM_SUB_FEATURES)
        importance = compute_sub_feature_importance(self.policy)
        values = [v for _, v in importance]
        self.assertEqual(values, sorted(values, reverse=True))


class TestStrategyRules(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()

    def test_no_rules_for_zero_weights(self):
        rules = generate_strategy_rules(self.policy)
        self.assertEqual(len(rules), 0)

    def test_strong_spread_generates_rule(self):
        # score_lead: strong positive for gain_food, strong negative for play_a_bird
        si = FEATURE_NAMES.index("score_lead")
        self.policy.weights[si, ACTION_INDEX["play_a_bird"]] = -1.5
        self.policy.weights[si, ACTION_INDEX["gain_food"]] = 1.0
        rules = generate_strategy_rules(self.policy, threshold=0.5)
        self.assertTrue(len(rules) >= 1)
        rule = rules[0]
        self.assertIsInstance(rule, StrategyRule)
        self.assertEqual(rule.feature_name, "score_lead")
        self.assertEqual(rule.action_name, "gain_food")
        self.assertAlmostEqual(rule.magnitude, 2.5)

    def test_threshold_controls_sensitivity(self):
        self.policy.weights[0, 0] = 0.6
        self.policy.weights[0, 1] = -0.3
        rules_low = generate_strategy_rules(self.policy, threshold=0.5)
        rules_high = generate_strategy_rules(self.policy, threshold=1.0)
        self.assertGreaterEqual(len(rules_low), len(rules_high))

    def test_sub_decision_rule_generated(self):
        # Strong weight on option_points
        self.policy.sub_weights[NUM_FEATURES] = 3.0
        rules = generate_strategy_rules(self.policy, threshold=0.5)
        sub_rules = [r for r in rules if r.action_name is None]
        self.assertTrue(len(sub_rules) >= 1)
        self.assertEqual(sub_rules[0].feature_name, "option_points")

    def test_negative_sub_weight_says_avoids(self):
        self.policy.sub_weights[NUM_FEATURES + OPTION_FEATURE_NAMES.index("option_is_deck")] = -1.0
        rules = generate_strategy_rules(self.policy, threshold=0.5)
        sub_rules = [r for r in rules if r.feature_name == "option_is_deck"]
        self.assertEqual(len(sub_rules), 1)
        self.assertIn("avoids", sub_rules[0].behavior)

    def test_rules_sorted_by_magnitude(self):
        self.policy.weights = np.random.RandomState(42).randn(NUM_FEATURES, 3) * 2
        rules = generate_strategy_rules(self.policy, threshold=0.5)
        magnitudes = [r.magnitude for r in rules]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))

    def test_format_strategy_summary_empty(self):
        result = format_strategy_summary([])
        self.assertIn("No significant", result)

    def test_format_strategy_summary_nonempty(self):
        rules = [StrategyRule("When ahead", "prefers to gain food", 2.5, "score_lead", "gain_food")]
        result = format_strategy_summary(rules)
        self.assertIn("1 rules discovered", result)
        self.assertIn("When ahead", result)
        self.assertIn("gain food", result)


class TestDecisionTrace(unittest.TestCase):
    def setUp(self):
        self.policy = LinearPolicy()
        self.policy.weights = np.random.RandomState(7).randn(NUM_FEATURES, 3)
        self.policy.sub_weights = np.random.RandomState(8).randn(NUM_SUB_FEATURES)
        self.game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        self.state = self.game.game_state

    def test_trace_returns_three_actions(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        self.assertEqual(len(breakdowns), 3)
        actions = {b.action_name for b in breakdowns}
        self.assertEqual(actions, set(ACTION_INDEX.keys()))

    def test_contributions_sum_to_total(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        for b in breakdowns:
            contrib_sum = sum(c.contribution for c in b.contributions)
            self.assertAlmostEqual(contrib_sum, b.total_score, places=10)

    def test_probabilities_sum_to_one(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        total_prob = sum(b.probability for b in breakdowns)
        self.assertAlmostEqual(total_prob, 1.0, places=10)

    def test_contribution_equals_weight_times_value(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        for b in breakdowns:
            for c in b.contributions:
                self.assertAlmostEqual(c.contribution, c.weight * c.feature_value, places=10)

    def test_sorted_by_probability_descending(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        probs = [b.probability for b in breakdowns]
        self.assertEqual(probs, sorted(probs, reverse=True))

    def test_contributions_sorted_by_magnitude(self):
        breakdowns = trace_action_decision(self.policy, self.state)
        for b in breakdowns:
            magnitudes = [abs(c.contribution) for c in b.contributions]
            self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))

    def test_sub_decision_trace(self):
        tray_names = self.state.get_tray().see_birds_in_tray()
        options = tray_names + ["deck"]
        breakdowns = trace_sub_decision(self.policy, self.state, options)
        self.assertEqual(len(breakdowns), len(options))
        total_prob = sum(b.probability for b in breakdowns)
        self.assertAlmostEqual(total_prob, 1.0, places=10)

    def test_sub_decision_contributions_sum(self):
        options = self.state.get_tray().see_birds_in_tray()[:2]
        breakdowns = trace_sub_decision(self.policy, self.state, options)
        for b in breakdowns:
            contrib_sum = sum(c.contribution for c in b.contributions)
            self.assertAlmostEqual(contrib_sum, b.total_score, places=10)

    def test_create_sample_states_deterministic(self):
        states1 = create_sample_states(num_samples=2, seed=42)
        states2 = create_sample_states(num_samples=2, seed=42)
        self.assertEqual(len(states1), 2)
        # Same seed should produce same tray contents
        tray1 = states1[0].get_tray().see_birds_in_tray()
        tray2 = states2[0].get_tray().see_birds_in_tray()
        self.assertEqual(tray1, tray2)

    def test_create_sample_states_different_seeds_vary(self):
        states = create_sample_states(num_samples=3, seed=42)
        trays = [s.get_tray().see_birds_in_tray() for s in states]
        # At least two of the three should be different
        self.assertFalse(trays[0] == trays[1] == trays[2])


class TestCheckpointLoading(unittest.TestCase):
    def test_empty_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_checkpoint_weights(tmpdir)
            self.assertEqual(result["iterations"], [])

    def test_load_and_subsample(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 fake checkpoints
            for i in range(10):
                p = LinearPolicy()
                p.weights[:, 0] = float(i)
                p.save(os.path.join(tmpdir, f"policy_iter_{i * 10}.npz"))

            result = load_checkpoint_weights(tmpdir, max_checkpoints=5)
            self.assertEqual(len(result["iterations"]), 5)
            self.assertEqual(result["iterations"][0], 0)
            self.assertEqual(result["iterations"][-1], 90)
            self.assertEqual(result["action_weights"].shape[0], 5)

    def test_load_all_when_under_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                p = LinearPolicy()
                p.save(os.path.join(tmpdir, f"policy_iter_{i}.npz"))

            result = load_checkpoint_weights(tmpdir, max_checkpoints=50)
            self.assertEqual(len(result["iterations"]), 3)

    def test_iterations_sorted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in [50, 10, 30]:
                p = LinearPolicy()
                p.save(os.path.join(tmpdir, f"policy_iter_{i}.npz"))

            result = load_checkpoint_weights(tmpdir)
            self.assertEqual(result["iterations"], [10, 30, 50])


class TestWeightEvolution(unittest.TestCase):
    def setUp(self):
        self.checkpoint_data = {
            "iterations": [0, 10, 20],
            "action_weights": np.array(
                [
                    np.full((NUM_FEATURES, 3), 0.0),
                    np.full((NUM_FEATURES, 3), 1.0),
                    np.full((NUM_FEATURES, 3), 2.0),
                ]
            ),
            "sub_weights": np.array(
                [
                    np.full(NUM_SUB_FEATURES, 0.0),
                    np.full(NUM_SUB_FEATURES, 0.5),
                    np.full(NUM_SUB_FEATURES, 1.0),
                ]
            ),
        }

    def test_extract_action_weight(self):
        result = compute_weight_evolution(self.checkpoint_data, "food_supply", "play_a_bird")
        self.assertEqual(result["iterations"], [0, 10, 20])
        self.assertEqual(result["values"], [0.0, 1.0, 2.0])
        self.assertEqual(result["feature_name"], "food_supply")
        self.assertEqual(result["action_name"], "play_a_bird")

    def test_extract_sub_weight(self):
        result = compute_weight_evolution(self.checkpoint_data, "option_points")
        self.assertEqual(result["values"], [0.0, 0.5, 1.0])
        self.assertIsNone(result["action_name"])

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            compute_weight_evolution(self.checkpoint_data, "food_supply", "lay_eggs")

    def test_invalid_feature_raises(self):
        with self.assertRaises(ValueError):
            compute_weight_evolution(self.checkpoint_data, "nonexistent", "play_a_bird")


if __name__ == "__main__":
    unittest.main()
