import unittest

import numpy as np

from src.game import WingspanGame
from src.rl.featurizer import (
    FEATURE_NAMES,
    NUM_FEATURES,
    NUM_OPTION_FEATURES,
    OPTION_FEATURE_NAMES,
    featurize,
    featurize_option,
)


class TestFeaturizer(unittest.TestCase):
    def setUp(self):
        self.game = WingspanGame(num_players=2, num_turns=5, num_starting_cards=2)
        self.state = self.game.game_state

    def test_returns_correct_shape(self):
        features = featurize(self.state)
        self.assertEqual(features.shape, (NUM_FEATURES,))

    def test_feature_names_match_count(self):
        self.assertEqual(len(FEATURE_NAMES), NUM_FEATURES)

    def test_all_features_are_finite(self):
        features = featurize(self.state)
        self.assertTrue(np.all(np.isfinite(features)))

    def test_game_progress_at_start(self):
        features = featurize(self.state)
        self.assertEqual(features[FEATURE_NAMES.index("game_progress")], 0.0)

    def test_can_play_bird_with_food(self):
        features = featurize(self.state)
        can_play_idx = FEATURE_NAMES.index("can_play_bird")
        self.assertIn(features[can_play_idx], (0.0, 1.0))

    def test_features_change_after_turn(self):
        features_before = featurize(self.state)
        player = self.state.get_current_player()
        action = player.request_action(game_state=self.state)
        player.take_action(action=action, game_state=self.state)
        self.state.end_player_turn(player=player)
        features_after = featurize(self.state)
        self.assertFalse(np.array_equal(features_before, features_after))

    def test_hand_best_ratio(self):
        features = featurize(self.state)
        ratio_idx = FEATURE_NAMES.index("hand_best_ratio")
        self.assertGreaterEqual(features[ratio_idx], 0.0)

    def test_tray_best_ratio(self):
        features = featurize(self.state)
        ratio_idx = FEATURE_NAMES.index("tray_best_ratio")
        self.assertGreater(features[ratio_idx], 0.0)

    def test_no_feeder_food_feature(self):
        self.assertNotIn("feeder_food", FEATURE_NAMES)

    def test_score_lead_uses_live_scores(self):
        features = featurize(self.state)
        lead_idx = FEATURE_NAMES.index("score_lead")
        # Both players start with 0 score, lead should be 0
        self.assertEqual(features[lead_idx], 0.0)

    def test_hand_min_cost_zero_when_nothing_playable(self):
        # Drain all food so nothing is playable
        player = self.state.get_current_player()
        player.get_food_supply().decrement(player.get_food_supply().amount)
        features = featurize(self.state)
        min_cost_idx = FEATURE_NAMES.index("hand_min_cost")
        self.assertEqual(features[min_cost_idx], 0.0)


class TestFeaturizeOption(unittest.TestCase):
    def setUp(self):
        self.game = WingspanGame(num_players=2, num_turns=5, num_starting_cards=2)
        self.state = self.game.game_state

    def test_returns_correct_shape(self):
        features = featurize_option(self.state, "deck")
        self.assertEqual(features.shape, (NUM_OPTION_FEATURES,))

    def test_option_feature_names_match_count(self):
        self.assertEqual(len(OPTION_FEATURE_NAMES), NUM_OPTION_FEATURES)

    def test_deck_option_has_is_deck_flag(self):
        features = featurize_option(self.state, "deck")
        is_deck_idx = OPTION_FEATURE_NAMES.index("option_is_deck")
        self.assertEqual(features[is_deck_idx], 1.0)
        # All other features should be 0 for deck
        for i, val in enumerate(features):
            if i != is_deck_idx:
                self.assertEqual(val, 0.0)

    def test_bird_option_from_tray(self):
        tray_birds = self.state.get_tray().get_birds_in_tray()
        bird_name = tray_birds[0].get_name()
        features = featurize_option(self.state, bird_name)
        self.assertTrue(np.all(np.isfinite(features)))
        # Should not have is_deck flag
        is_deck_idx = OPTION_FEATURE_NAMES.index("option_is_deck")
        self.assertEqual(features[is_deck_idx], 0.0)
        # Should have positive points
        points_idx = OPTION_FEATURE_NAMES.index("option_points")
        self.assertGreaterEqual(features[points_idx], 0.0)

    def test_bird_option_from_hand(self):
        hand_birds = self.state.get_current_player().get_bird_hand().get_cards_in_hand()
        bird_name = hand_birds[0].get_name()
        features = featurize_option(self.state, bird_name)
        self.assertTrue(np.all(np.isfinite(features)))

    def test_unknown_bird_returns_zeros(self):
        features = featurize_option(self.state, "Nonexistent Bird")
        np.testing.assert_array_equal(features, np.zeros(NUM_OPTION_FEATURES))

    def test_affordable_flag(self):
        player = self.state.get_current_player()
        hand_birds = player.get_bird_hand().get_cards_in_hand()
        bird = hand_birds[0]
        affordable_idx = OPTION_FEATURE_NAMES.index("option_affordable")

        # With enough food
        player.get_food_supply().amount = 10
        features = featurize_option(self.state, bird.get_name())
        self.assertEqual(features[affordable_idx], 1.0)

        # With no food and bird costs > 0
        player.get_food_supply().amount = 0
        features = featurize_option(self.state, bird.get_name())
        if bird.get_food_cost() > 0:
            self.assertEqual(features[affordable_idx], 0.0)


if __name__ == "__main__":
    unittest.main()
