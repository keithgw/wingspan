import unittest
from unittest.mock import Mock, patch
from src.rl.mcts import State
from src.entities.bird import Bird
from src.entities.hand import BirdHand
from src.entities.deck import Deck
from src.entities.player import BotPlayer

class TestState(unittest.TestCase):
    def setUp(self):
        self.game_state = Mock()
        self.state = State(self.game_state)

    def test_state_initialization(self):
        self.assertEqual(self.state.game_state, self.game_state)

    def test_represent_bird_deck(self):
        self.game_state.get_bird_deck.return_value.get_count.return_value = 10
        self.assertEqual(self.state._represent_bird_deck(), 10)

    def test_represent_discard_pile(self):
        self.game_state.get_discard_pile.return_value.get_count.return_value = 5
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
        player = Mock()
        self.game_state.get_players.return_value = ['player1', 'player2', 'player3']
        self.game_state.get_game_turn.return_value = 1
        opponents = self.state._get_opponents(player)
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
        self.game_state.get_num_turns.return_value = 10
        self.game_state.get_game_turn.return_value = 5
        self.game_state.get_phase.return_value = 'choose_action'
        self.game_state.tray.to_representation.return_value = frozenset([(1, 1,), (1, 2), (3, 1)])
        self.game_state.bird_feeder.to_representation.return_value = 5
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
        game_state = self.state.from_representation(representation)
        self.assertEqual(game_state.get_num_turns(), 10)

if __name__ == '__main__':
    unittest.main()