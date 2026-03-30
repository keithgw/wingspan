import unittest

import numpy as np

from src.entities.bird import Bird
from src.game import WingspanGame
from src.rl.featurizer import (
    FEATURE_NAMES,
    NUM_FEATURES,
    NUM_OPTION_FEATURES,
    OPTION_FEATURE_NAMES,
    _max_achievable_vp,
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

    def test_turns_remaining_at_start(self):
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("turns_remaining")
        self.assertEqual(features[idx], 1.0)

    def test_max_achievable_vp_positive_with_hand(self):
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("max_achievable_vp")
        # With food and birds in hand at game start, should be positive
        player = self.state.get_current_player()
        hand = player.get_bird_hand().get_cards_in_hand()
        food = player.get_food_supply().amount
        playable = [b for b in hand if food >= b.get_food_cost()]
        if playable:
            self.assertGreater(features[idx], 0.0)

    def test_unseen_mean_ratio_is_bounded(self):
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("unseen_mean_ratio")
        # Should be between 0 and 1 (normalized by /5.0)
        self.assertGreater(features[idx], 0.0)
        self.assertLessEqual(features[idx], 1.0)

    def test_prob_draw_affordable_at_start(self):
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("prob_draw_affordable")
        # At start with 3 food, most cards (cost 0-3) are affordable
        self.assertGreater(features[idx], 0.5)

    def test_food_gap_for_best_with_low_food(self):
        player = self.state.get_current_player()
        player.get_food_supply().amount = 0
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("food_gap_for_best")
        # With 0 food, gap should be positive if hand has any birds with cost > 0
        hand_birds = player.get_bird_hand().get_cards_in_hand()
        max_cost = max((b.get_food_cost() for b in hand_birds), default=0)
        self.assertAlmostEqual(features[idx], max_cost / 5.0)

    def test_food_gap_for_best_with_plenty_food(self):
        player = self.state.get_current_player()
        player.get_food_supply().amount = 10
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("food_gap_for_best")
        self.assertEqual(features[idx], 0.0)

    def test_vp_at_stake_matches_best_immediate(self):
        features = featurize(self.state)
        vp_idx = FEATURE_NAMES.index("vp_at_stake")
        biv_idx = FEATURE_NAMES.index("best_immediate_vp")
        self.assertEqual(features[vp_idx], features[biv_idx])

    def test_endgame_flag_at_start(self):
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("endgame_flag")
        # 5 turns remaining at start, should not be endgame
        self.assertEqual(features[idx], 0.0)

    def test_endgame_flag_near_end(self):
        # Burn turns until <= 3 remain
        player = self.state.get_current_player()
        while player.get_turns_remaining() > 3:
            action = player.request_action(game_state=self.state)
            player.take_action(action=action, game_state=self.state)
            self.state.end_player_turn(player=player)
        features = featurize(self.state)
        idx = FEATURE_NAMES.index("endgame_flag")
        self.assertEqual(features[idx], 1.0)

    def test_urgency_zero_when_leading(self):
        features = featurize(self.state)
        lead_idx = FEATURE_NAMES.index("score_lead")
        urgency_idx = FEATURE_NAMES.index("urgency")
        if features[lead_idx] >= 0:
            self.assertEqual(features[urgency_idx], 0.0)

    def test_hand_min_cost_zero_when_nothing_playable(self):
        # Drain all food so nothing is playable
        player = self.state.get_current_player()
        player.get_food_supply().decrement(player.get_food_supply().amount)
        features = featurize(self.state)
        min_cost_idx = FEATURE_NAMES.index("hand_min_cost")
        self.assertEqual(features[min_cost_idx], 0.0)


class TestMaxAchievableVP(unittest.TestCase):
    def test_no_turns_returns_zero(self):
        hand = [Bird("A", 5, 2)]
        self.assertEqual(_max_achievable_vp(hand, food=3, board_slots_left=5, turns_left=0), 0.0)

    def test_no_slots_returns_zero(self):
        hand = [Bird("A", 5, 2)]
        self.assertEqual(_max_achievable_vp(hand, food=3, board_slots_left=0, turns_left=5), 0.0)

    def test_empty_hand_returns_zero(self):
        self.assertEqual(_max_achievable_vp([], food=3, board_slots_left=5, turns_left=5), 0.0)

    def test_one_affordable_bird_one_turn(self):
        hand = [Bird("A", 5, 2)]
        self.assertEqual(_max_achievable_vp(hand, food=2, board_slots_left=5, turns_left=1), 5.0)

    def test_one_bird_needs_food_turn(self):
        # Cost 3, have 1 food -> need 2 food turns + 1 play turn = 3 turns
        hand = [Bird("A", 7, 3)]
        self.assertEqual(_max_achievable_vp(hand, food=1, board_slots_left=5, turns_left=3), 7.0)
        # Only 2 turns available: not enough
        self.assertEqual(_max_achievable_vp(hand, food=1, board_slots_left=5, turns_left=2), 0.0)

    def test_greedy_picks_highest_vp_first(self):
        hand = [Bird("Low", 2, 1), Bird("High", 8, 1)]
        # 2 turns, 1 food each -> plays High first, then Low
        self.assertEqual(_max_achievable_vp(hand, food=2, board_slots_left=5, turns_left=2), 10.0)

    def test_slot_limit_caps_plays(self):
        hand = [Bird("A", 5, 1), Bird("B", 3, 1), Bird("C", 2, 1)]
        # 3 food, 3 turns, but only 1 slot
        self.assertEqual(_max_achievable_vp(hand, food=3, board_slots_left=1, turns_left=3), 5.0)

    def test_food_budget_across_multiple_birds(self):
        # Bird A: 6 VP, cost 2. Bird B: 4 VP, cost 3.
        # Have 3 food, 3 turns.
        # Play A (cost 2, 1 turn, food left 1), then need 2 more food for B (2 turns) + 1 play = 3 turns. Only 2 left.
        # So only A is playable.
        hand = [Bird("A", 6, 2), Bird("B", 4, 3)]
        self.assertEqual(_max_achievable_vp(hand, food=3, board_slots_left=5, turns_left=3), 6.0)
        # With 5 turns: play A (1 turn, food=1), gain 2 food (2 turns, food=3), play B (1 turn) = 4 turns total
        self.assertEqual(_max_achievable_vp(hand, food=3, board_slots_left=5, turns_left=5), 10.0)

    def test_free_bird_costs_one_turn(self):
        hand = [Bird("Free", 2, 0)]
        self.assertEqual(_max_achievable_vp(hand, food=0, board_slots_left=5, turns_left=1), 2.0)


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
