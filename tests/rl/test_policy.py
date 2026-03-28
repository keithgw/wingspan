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


class TestBackpropagate(unittest.TestCase):
    def setUp(self):
        self.policy = MCTSPolicy()

    def test_updates_single_node(self):
        node = Node(state=Mock(), parent=None)
        self.policy._backpropagate(node, 1.0)
        self.assertEqual(node.num_visits, 1)
        self.assertEqual(node.total_reward, 1.0)

    def test_propagates_to_root(self):
        root = Node(state=Mock(), parent=None)
        child = Node(state=Mock(), parent=root)
        grandchild = Node(state=Mock(), parent=child)

        self.policy._backpropagate(grandchild, 1.0)

        self.assertEqual(grandchild.num_visits, 1)
        self.assertEqual(child.num_visits, 1)
        self.assertEqual(root.num_visits, 1)
        self.assertEqual(root.total_reward, 1.0)

    def test_accumulates_over_multiple_calls(self):
        root = Node(state=Mock(), parent=None)
        child = Node(state=Mock(), parent=root)

        self.policy._backpropagate(child, 1.0)
        self.policy._backpropagate(child, 0.0)

        self.assertEqual(child.num_visits, 2)
        self.assertEqual(child.total_reward, 1.0)
        self.assertEqual(root.num_visits, 2)
        self.assertEqual(root.total_reward, 1.0)


class TestExpand(unittest.TestCase):
    def setUp(self):
        self.policy = MCTSPolicy()
        self.policy._mcts_player_index = 0
        game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        self.mcts_state = MCTSGameState.from_game_state(game.game_state)

    def test_creates_children_for_choose_action(self):
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        # Should have children for each legal action (at least gain_food + draw_a_bird)
        self.assertGreaterEqual(len(leaf.children), 2)
        actions = [child.action for child in leaf.children]
        self.assertIn("gain_food", actions)

    def test_returns_one_of_the_children(self):
        leaf = Node(state=self.mcts_state)
        result = self.policy._expand(leaf)
        self.assertIn(result, leaf.children)

    def test_children_have_parent_set(self):
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        for child in leaf.children:
            self.assertIs(child.parent, leaf)

    def test_terminal_returns_leaf(self):
        # Set game_turn to make game over
        self.mcts_state.game_turn = self.mcts_state.num_turns * self.mcts_state.num_players
        leaf = Node(state=self.mcts_state)
        result = self.policy._expand(leaf)
        self.assertIs(result, leaf)
        self.assertEqual(len(leaf.children), 0)

    def test_does_not_mutate_leaf_state(self):
        leaf = Node(state=self.mcts_state)
        repr_before = leaf.state.to_representation()
        self.policy._expand(leaf)
        repr_after = leaf.state.to_representation()
        self.assertEqual(repr_before, repr_after)

    def test_gain_food_child_has_more_food(self):
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        gain_food_child = next(c for c in leaf.children if c.action == "gain_food")
        # The child's current player should have advanced (turn ended), so check
        # that the state has progressed
        self.assertGreater(gain_food_child.state.game_turn, leaf.state.game_turn)

    def test_play_a_bird_child_is_mid_turn(self):
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        play_children = [c for c in leaf.children if c.action == "play_a_bird"]
        if play_children:
            self.assertEqual(play_children[0].state.phase, CHOOSE_A_BIRD_TO_PLAY)

    def test_expand_choose_a_bird_to_play(self):
        self.mcts_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        # Children should be one per playable bird
        self.assertGreater(len(leaf.children), 0)
        for child in leaf.children:
            # Each child should have the turn ended (phase reset)
            self.assertEqual(child.state.phase, "choose_action")

    def test_expand_choose_a_bird_to_draw(self):
        self.mcts_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)
        leaf = Node(state=self.mcts_state)
        self.policy._expand(leaf)
        self.assertGreater(len(leaf.children), 0)
        actions = [c.action for c in leaf.children]
        # Should include "deck" since deck is non-empty
        self.assertIn("deck", actions)


class TestRunSimulationsIntegration(unittest.TestCase):
    def test_builds_tree_and_selects_best(self):
        policy = MCTSPolicy(num_simulations=20)
        game = WingspanGame(num_players=2, num_turns=2, num_starting_cards=2)
        mcts_state = MCTSGameState.from_game_state(game.game_state)
        policy._mcts_player_index = 0

        root = Node(state=mcts_state)
        policy._run_simulations(root, 20)

        # Root should have been visited 20 times
        self.assertEqual(root.num_visits, 20)
        # Root should have children
        self.assertGreater(len(root.children), 0)
        # Best child should be determinable
        best = policy._best_child(root)
        self.assertIn(best.action, ["play_a_bird", "gain_food", "draw_a_bird"])


if __name__ == "__main__":
    unittest.main()
