import unittest
from unittest.mock import Mock, patch

from src.constants import CHOOSE_A_BIRD_TO_DRAW, CHOOSE_ACTION
from src.entities.bird import Bird
from src.entities.deck import Deck
from src.entities.game_state import GameState, MCTSGameState
from src.entities.hand import BirdHand
from src.entities.player import BotPlayer
from src.rl.policy import RandomPolicy


class TestGameState(unittest.TestCase):
    def setUp(self):
        self.num_turns = 10
        self.players = [Mock(), Mock(), Mock(), Mock()]
        self.game_state = GameState(
            num_turns=self.num_turns,
            bird_deck=Mock(),
            discard_pile=Mock(),
            tray=Mock(),
            bird_feeder=Mock(),
            players=self.players,
        )

    def test_get_num_turns(self):
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_get_phase(self):
        self.assertEqual(self.game_state.get_phase(), CHOOSE_ACTION)

    def test_set_phase_valid(self):
        self.game_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)
        self.assertEqual(self.game_state.get_phase(), CHOOSE_A_BIRD_TO_DRAW)

    def test_set_phase_invalid(self):
        with self.assertRaises(ValueError):
            self.game_state.set_phase("invalid_phase")

    def test_get_current_player_start(self):
        self.assertEqual(self.game_state.get_current_player(), self.players[0])

    def test_get_current_player_after_one_turn(self):
        self.game_state.end_player_turn(self.players[0])
        self.assertEqual(self.game_state.get_current_player(), self.players[1])

    def test_end_player_turn_refills_tray(self):
        self.game_state.tray.is_not_full.return_value = True
        self.game_state.end_player_turn(player=self.players[0])
        self.game_state.tray.refill.assert_called_once_with(self.game_state.bird_deck)

    def test_end_player_turn_increments_game_turn(self):
        self.game_state.end_player_turn(player=self.players[0])
        self.assertEqual(self.game_state.game_turn, 1)

    def test_end_player_turn_calls_player_end_turn(self):
        self.game_state.end_player_turn(player=self.players[0])
        self.players[0].end_turn.assert_called_once()

    def test_num_turns_does_not_change(self):
        self.game_state.end_player_turn(self.players[0])
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_is_game_over(self):
        for turn in range(self.num_turns):
            for i in range(self.game_state.num_players):
                self.game_state.end_player_turn(player=self.players[i])
                if turn < self.num_turns - 1 or i < self.game_state.num_players - 1:
                    self.assertFalse(self.game_state.is_game_over())
        self.assertTrue(self.game_state.is_game_over())


class TestMCTSGameState(unittest.TestCase):
    def setUp(self):
        self.state = MCTSGameState.from_game_state(
            GameState(
                num_turns=10,
                bird_deck=Mock(),
                discard_pile=Mock(),
                tray=Mock(),
                bird_feeder=Mock(),
                players=[Mock(), Mock(), Mock(), Mock()],
            )
        )

    def test_represent_bird_deck(self):
        self.state.bird_deck.get_count.return_value = 10
        self.assertEqual(self.state._represent_bird_deck(), 10)

    def test_represent_discard_pile(self):
        self.state.discard_pile.get_count.return_value = 5
        self.assertEqual(self.state._represent_discard_pile(), 5)

    def test_represent_player_full(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = 3
        player.get_game_board.return_value.to_representation.return_value = ((0, 0),)
        player.get_bird_hand.return_value.to_representation.return_value = ((3, 1), (5, 1))
        rep = self.state._represent_player(player, full=True)
        expected = frozenset([("food_supply", 3), ("game_board", ((0, 0),)), ("hand", ((3, 1), (5, 1)))])
        self.assertEqual(rep, expected)

    def test_represent_player_partial(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = 3
        player.get_game_board.return_value.to_representation.return_value = ((0, 0),)
        player.get_bird_hand.return_value.get_count.return_value = 2
        rep = self.state._represent_player(player, full=False)
        expected = frozenset([("food_supply", 3), ("game_board", ((0, 0),)), ("hand", 2)])
        self.assertEqual(rep, expected)

    def test_get_opponents(self):
        self.state.players = ["player1", "player2", "player3"]
        self.state.game_turn = 1
        self.assertEqual(self.state._get_opponents(), ["player3", "player1"])

    def test_reorder_players(self):
        current = Mock()
        opponents = ["opp1", "opp2", "opp3"]
        reordered = self.state._reorder_players(current, opponents, game_turn=5)
        self.assertEqual(reordered, ["opp3", current, "opp1", "opp2"])

    def test_get_turns_remaining(self):
        self.assertEqual(self.state._get_turns_remaining(num_turns=10, game_turn=23, num_players=4), 5)

    def test_construct_player(self):
        hand = BirdHand()
        deck = Deck()
        deck.add_card(Bird("bird", 1, 1))
        rep = {"food_supply": 10, "game_board": ((0, 0), (1, 1))}
        player = self.state._construct_player(
            hand=hand, representation=rep, deck=deck, game_turn=1, num_turns=10, num_players=2, name="test"
        )
        self.assertIsInstance(player, BotPlayer)
        self.assertEqual(player.name, "test")

    def test_to_representation(self):
        self.state.num_turns = 10
        self.state.game_turn = 5
        self.state.phase = "choose_action"
        self.state.tray.to_representation.return_value = ((1, 1), (1, 2), (3, 1))
        self.state.bird_feeder.to_representation.return_value = 5
        player_rep = frozenset([("food_supply", 3), ("game_board", ((0, 0),)), ("hand", 2)])

        with patch.multiple(
            self.state,
            _represent_bird_deck=Mock(return_value=20),
            _represent_discard_pile=Mock(return_value=3),
            _represent_player=Mock(return_value=player_rep),
            _get_opponents=Mock(return_value=["opp1", "opp2"]),
        ):
            rep = self.state.to_representation()

        rep_dict = dict(rep)
        self.assertEqual(rep_dict["num_turns"], 10)
        self.assertEqual(rep_dict["game_turn"], 5)
        self.assertEqual(rep_dict["bird_deck"], 20)

    def test_from_representation_round_trip(self):
        # Board capacity=5: 0 birds + 5 empty. Tray capacity=3: 3 birds.
        # 180 total birds: 3 tray + 2 current hand + 2+2 opponent hands + 20 deck + 151 discard = 180
        board_rep = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
        tray_rep = ((1, 1), (1, 2), (3, 1))
        hand_rep = ((3, 1), (5, 1))
        rep = frozenset(
            [
                ("num_turns", 10),
                ("game_turn", 5),
                ("phase", "choose_action"),
                ("bird_deck", 20),
                ("discard_pile", 151),
                ("tray", tray_rep),
                ("bird_feeder", 5),
                (
                    "current_player",
                    frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", hand_rep)]),
                ),
                (
                    "opponents",
                    (
                        frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", 2)]),
                        frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", 2)]),
                    ),
                ),
            ]
        )
        game_state = MCTSGameState.from_representation(rep)
        self.assertEqual(game_state.to_representation(), rep)

    def _make_representation(self):
        board_rep = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
        tray_rep = ((1, 1), (1, 2), (3, 1))
        hand_rep = ((3, 1), (5, 1))
        return frozenset(
            [
                ("num_turns", 10),
                ("game_turn", 5),
                ("phase", "choose_action"),
                ("bird_deck", 20),
                ("discard_pile", 151),
                ("tray", tray_rep),
                ("bird_feeder", 5),
                (
                    "current_player",
                    frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", hand_rep)]),
                ),
                (
                    "opponents",
                    (
                        frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", 2)]),
                        frozenset([("food_supply", 3), ("game_board", board_rep), ("hand", 2)]),
                    ),
                ),
            ]
        )

    def test_from_representation_default_uses_random_policy(self):
        rep = self._make_representation()
        game_state = MCTSGameState.from_representation(rep)
        for player in game_state.get_players():
            self.assertIsInstance(player.policy, RandomPolicy)

    def test_from_representation_with_playout_policy(self):
        rep = self._make_representation()
        custom_policy = Mock()
        game_state = MCTSGameState.from_representation(rep, playout_policy=custom_policy)
        for player in game_state.get_players():
            self.assertIs(player.policy, custom_policy)

    def test_from_game_state(self):
        gs = GameState(
            num_turns=10,
            bird_deck=Deck(),
            discard_pile=Deck(),
            tray=Mock(),
            bird_feeder=Mock(),
            players=[Mock()],
            game_turn=1,
            phase=CHOOSE_ACTION,
        )
        mcts = MCTSGameState.from_game_state(gs)
        self.assertEqual(mcts.num_turns, gs.num_turns)
        self.assertEqual(mcts.bird_deck, gs.bird_deck)
        self.assertEqual(mcts.game_turn, gs.game_turn)


if __name__ == "__main__":
    unittest.main()
