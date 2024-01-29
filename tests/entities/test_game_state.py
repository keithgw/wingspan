import unittest
from src.constants import CHOOSE_ACTION, CHOOSE_A_BIRD_TO_DRAW
from src.entities.game_state import GameState, MCTSGameState
from src.entities.hand import BirdHand
from src.entities.deck import Deck
from src.entities.bird import Bird
from src.entities.player import BotPlayer
from unittest.mock import Mock, patch

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.num_turns = 10
        self.players = [Mock(), Mock(), Mock(), Mock()]
        self.game_state = GameState(num_turns=self.num_turns, bird_deck=Mock(), discard_pile=Mock(), tray=Mock(), bird_feeder=Mock(), players=self.players)  # Example initialization with 10 turns and 4 players

    def test_get_num_turns(self):
        self.assertEqual(self.game_state.get_num_turns(), self.num_turns)

    def test_get_phase(self):
        self.assertEqual(self.game_state.get_phase(), CHOOSE_ACTION)

    def test_set_phase_valid(self):
        self.game_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)
        self.assertEqual(self.game_state.get_phase(), CHOOSE_A_BIRD_TO_DRAW)

    def test_set_phase_invalid(self):
        with self.assertRaises(ValueError):
            self.game_state.set_phase('invalid_phase')

    def test_get_current_player_start(self):
        self.assertEqual(self.game_state.get_current_player(), self.players[0])

    def test_get_current_player_after_one_turn(self):
        self.game_state.end_player_turn(self.players[0])
        self.assertEqual(self.game_state.get_current_player(), self.players[1])

    def test_end_player_turn_refills_tray(self):
            self.game_state.end_player_turn(player=self.players[0])

            # tray is empty, check that tray.refill() is called
            self.game_state.tray.is_not_full.return_value = True
            self.game_state.tray.refill.assert_called_once_with(self.game_state.bird_deck)

    def test_end_player_turn_increments_game_turn(self):
            self.game_state.end_player_turn(player=self.players[0])

            # game turn increments
            self.assertEqual(self.game_state.game_turn, 1)

    def test_end_player_turn_calls_player_end_turn(self):
            self.game_state.end_player_turn(player=self.players[0])

            # player.end_turn() is called
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
        self.state = MCTSGameState.from_game_state(GameState(num_turns=10, 
                                                             bird_deck=Mock(), 
                                                             discard_pile=Mock(), 
                                                             tray=Mock(), 
                                                             bird_feeder=Mock(), 
                                                             players=[Mock(), Mock(), Mock(), Mock()]))

    def test_represent_bird_deck(self):
        self.state.bird_deck.get_count.return_value = 10
        self.assertEqual(self.state._represent_bird_deck(), 10)

    def test_represent_discard_pile(self):
        self.state.discard_pile.get_count.return_value = 5
        self.assertEqual(self.state._represent_discard_pile(), 5)

    def test_represent_player_full(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = 3
        player.get_game_board.return_value.to_representation.return_value = frozenset([(0, 0), (0, 0)])
        player.get_bird_hand.return_value.to_representation.return_value = frozenset([(5, 1), (3, 1)])
        representation = self.state._represent_player(player, full=True)
        expected_representation = frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', frozenset([(5, 1), (3, 1)]))])   
        self.assertEqual(representation, expected_representation)

    def test_represent_player_partial(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = 3
        player.get_game_board.return_value.to_representation.return_value = frozenset([(0, 0), (0, 0)])
        player.get_bird_hand.return_value.get_count.return_value = 2
        representation = self.state._represent_player(player, full=False)
        expected_representation = frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])
        self.assertEqual(representation, expected_representation)

    def test_get_opponents(self):
        self.state.players = ['player1', 'player2', 'player3']
        self.state.game_turn = 1
        opponents = self.state._get_opponents()
        self.assertEqual(opponents, ['player3', 'player1'])

    def test_reorder_players(self):
        current_player = Mock()
        opponents = ['opponent1', 'opponent2', 'opponent3']
        game_turn = 5
        reordered_players = self.state._reorder_players(current_player, opponents, game_turn)
        self.assertEqual(reordered_players, ['opponent3', current_player, 'opponent1', 'opponent2'])

    def test_get_turns_remaining(self):
        num_turns = 10
        game_turn = 23
        num_players = 4
        turns_remaining = self.state._get_turns_remaining(num_turns, game_turn, num_players)
        self.assertEqual(turns_remaining, 5)

    def test_construct_player(self):
        hand = BirdHand()
        representation = {
            'food_supply': 10,
            'game_board': frozenset([(1, 1), (0, 0)])
        }
        deck = Deck()
        deck.add_card(Bird("bird", 1, 1))
        game_turn = 1
        num_turns = 10
        num_players = 2
        name = "test_player"

        player = self.state._construct_player(
            hand=hand,
            representation=representation,
            deck=deck,
            game_turn=game_turn,
            num_turns=num_turns,
            num_players=num_players,
            name=name
        )
        self.assertIsInstance(player, BotPlayer)
        self.assertEqual(player.name, name)
        self.assertEqual(player.bird_hand, hand)
        self.assertEqual(player.food_supply.to_representation(), representation['food_supply'])
        self.assertEqual(player.game_board.to_representation(), representation['game_board'])

    def test_to_representation(self):
        # mock game state return values
        self.state.num_turns = 10
        self.state.game_turn = 5
        self.state.phase = 'choose_action'
        self.state.tray.to_representation.return_value = frozenset([(1, 1,), (1, 2), (3, 1)])
        self.state.bird_feeder.to_representation.return_value = 5
        player_representation = frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])

        # mock state return values
        with patch.multiple(self.state, 
                            _represent_bird_deck=Mock(return_value=20), 
                            _represent_discard_pile=Mock(return_value=3), 
                            _represent_player=Mock(return_value=player_representation),
                            _get_opponents=Mock(return_value=['opponent1', 'opponent2'])
                            ) as mocks:
            representation = self.state.to_representation()
        
        # construct expected representation
        expected_representation = frozenset([
            ('num_turns', 10),
            ('game_turn', 5),
            ('phase', 'choose_action'),
            ('bird_deck', 20),
            ('discard_pile', 3),
            ('tray', frozenset([(1, 1,), (1, 2), (3, 1)])),
            ('bird_feeder', 5),
            ('current_player', frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])),
            ('opponents', (frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)]), 
                           frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])
            ))
        ])
        self.assertEqual(representation, expected_representation)

    def test_from_representation(self):
        representation = frozenset([
            ('num_turns', 10),
            ('game_turn', 5),
            ('phase', 'choose_action'),
            ('bird_deck', 20),
            ('discard_pile', 151),
            ('tray', frozenset([(1, 1,), (1, 2), (3, 1)])),
            ('bird_feeder', 5),
            ('current_player', frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', frozenset([(5, 1), (3, 1)]))])),
            ('opponents', (frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)]), 
                           frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])
            ))
        ])
        game_state = MCTSGameState.from_representation(representation)
        self.assertEqual(game_state.to_representation(), representation)

    def test_from_game_state(self):
        # Create a GameState object
        game_state = GameState(num_turns=10, bird_deck=Deck(), discard_pile=Deck(), tray=Mock(), bird_feeder=Mock(), players=[Mock()], game_turn=1, phase=CHOOSE_ACTION)

        # Create a MCTSGameState object from the GameState object
        mcts_game_state = MCTSGameState.from_game_state(game_state)

        # Check that the MCTSGameState object has the same attribute values as the GameState object
        self.assertEqual(mcts_game_state.num_turns, game_state.num_turns)
        self.assertEqual(mcts_game_state.bird_deck, game_state.bird_deck)
        self.assertEqual(mcts_game_state.discard_pile, game_state.discard_pile)
        self.assertEqual(mcts_game_state.tray, game_state.tray)
        self.assertEqual(mcts_game_state.bird_feeder, game_state.bird_feeder)
        self.assertEqual(mcts_game_state.players, game_state.players)
        self.assertEqual(mcts_game_state.game_turn, game_state.game_turn)
        self.assertEqual(mcts_game_state.phase, game_state.phase)

if __name__ == '__main__':
    unittest.main()