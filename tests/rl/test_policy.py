import unittest
from io import StringIO
from unittest.mock import Mock, patch

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_A_BIRD_TO_PLAY
from src.entities.game_state import MCTSGameState
from src.game import WingspanGame
from src.rl.mcts import Node
from src.rl.policy import MCTSPolicy, RandomPolicy


class TestRandomPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomPolicy()

    @patch("src.rl.policy.np.random.choice", return_value="gain_food")
    def test_policy_choose_action(self, mock_choice):
        state = Mock()
        state.phase = "choose_action"
        actions = ["play_a_bird", "gain_food", "draw_a_bird"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "gain_food")

    @patch("src.rl.policy.np.random.choice", return_value="Osprey")
    def test_policy_choose_a_bird_to_play(self, mock_choice):
        state = Mock()
        state.phase = "choose_a_bird_to_play"
        actions = ["Osprey", "Cardinal"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "Osprey")

    @patch("src.rl.policy.np.random.choice", return_value="deck")
    def test_policy_choose_a_bird_to_draw(self, mock_choice):
        state = Mock()
        state.phase = "choose_a_bird_to_draw"
        actions = ["Blue Jay", "deck"]
        result = self.policy(state, actions)
        mock_choice.assert_called_once_with(actions)
        self.assertEqual(result, "deck")

    def test_call_dispatches_by_phase(self):
        for phase in ["choose_action", "choose_a_bird_to_play", "choose_a_bird_to_draw"]:
            state = Mock()
            state.phase = phase
            actions = ["action1", "action2"]
            result = self.policy(state, actions)
            self.assertIn(result, actions)


class TestMCTSPolicyPlayout(unittest.TestCase):
    def setUp(self):
        self.policy = MCTSPolicy()
        game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        self.mcts_state = MCTSGameState.from_game_state(game.game_state)
        self.policy._mcts_player_index = 0

    def test_playout_returns_valid_reward(self):
        node = Node(state=self.mcts_state)
        reward = self.policy._playout(node)
        self.assertIn(reward, (0.0, 0.5, 1.0))

    def test_playout_does_not_mutate_node_state(self):
        node = Node(state=self.mcts_state)
        repr_before = node.state.to_representation()
        self.policy._playout(node)
        repr_after = node.state.to_representation()
        self.assertEqual(repr_before, repr_after)

    def test_playout_mid_turn_choose_a_bird_to_play(self):
        self.mcts_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
        node = Node(state=self.mcts_state)
        reward = self.policy._playout(node)
        self.assertIn(reward, (0.0, 0.5, 1.0))

    def test_playout_mid_turn_choose_a_bird_to_draw(self):
        self.mcts_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)
        node = Node(state=self.mcts_state)
        reward = self.policy._playout(node)
        self.assertIn(reward, (0.0, 0.5, 1.0))

    def test_playout_suppresses_stdout(self):
        node = Node(state=self.mcts_state)
        captured = StringIO()
        with patch("sys.stdout", captured):
            self.policy._playout(node)
        self.assertEqual(captured.getvalue(), "")


class TestComputeReward(unittest.TestCase):
    def setUp(self):
        self.policy = MCTSPolicy()

    def test_win(self):
        self.policy._mcts_player_index = 0
        sim_state = Mock()
        p0, p1 = Mock(), Mock()
        p0.get_score.return_value = 10
        p1.get_score.return_value = 5
        sim_state.get_players.return_value = [p0, p1]
        self.assertEqual(self.policy._compute_reward(sim_state), 1.0)

    def test_loss(self):
        self.policy._mcts_player_index = 0
        sim_state = Mock()
        p0, p1 = Mock(), Mock()
        p0.get_score.return_value = 3
        p1.get_score.return_value = 10
        sim_state.get_players.return_value = [p0, p1]
        self.assertEqual(self.policy._compute_reward(sim_state), 0.0)

    def test_tie(self):
        self.policy._mcts_player_index = 0
        sim_state = Mock()
        p0, p1 = Mock(), Mock()
        p0.get_score.return_value = 7
        p1.get_score.return_value = 7
        sim_state.get_players.return_value = [p0, p1]
        self.assertEqual(self.policy._compute_reward(sim_state), 0.5)


if __name__ == "__main__":
    unittest.main()
