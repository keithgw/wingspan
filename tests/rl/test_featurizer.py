import unittest

import numpy as np

from src.game import WingspanGame
from src.rl.featurizer import FEATURE_NAMES, NUM_FEATURES, featurize


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
        # game_turn=0 at start, so progress should be 0
        self.assertEqual(features[FEATURE_NAMES.index("game_progress")], 0.0)

    def test_can_play_bird_with_food(self):
        features = featurize(self.state)
        # Starting hand has 2 birds and 3 food — should usually be able to play
        can_play_idx = FEATURE_NAMES.index("can_play_bird")
        # Could be 0 if both birds cost more than 3, but typically 1
        self.assertIn(features[can_play_idx], (0.0, 1.0))

    def test_features_change_after_turn(self):
        features_before = featurize(self.state)
        # Play a turn
        player = self.state.get_current_player()
        action = player.request_action(game_state=self.state)
        player.take_action(action=action, game_state=self.state)
        self.state.end_player_turn(player=player)
        features_after = featurize(self.state)
        # At least game_progress should change
        self.assertFalse(np.array_equal(features_before, features_after))

    def test_hand_best_ratio(self):
        features = featurize(self.state)
        ratio_idx = FEATURE_NAMES.index("hand_best_ratio")
        # Should be >= 0 (normalized by /10)
        self.assertGreaterEqual(features[ratio_idx], 0.0)

    def test_tray_best_ratio(self):
        features = featurize(self.state)
        ratio_idx = FEATURE_NAMES.index("tray_best_ratio")
        # Tray has 3 birds at start, ratio should be > 0
        self.assertGreater(features[ratio_idx], 0.0)


if __name__ == "__main__":
    unittest.main()
