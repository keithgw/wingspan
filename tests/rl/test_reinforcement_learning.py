import unittest
from unittest.mock import Mock
from src.entities.bird import Bird
from src.entities.hand import BirdHand
from src.entities.deck import Deck
from src.entities.player import BotPlayer
from src.rl.reinforcement_learning import State, RandomPolicy

class TestState(unittest.TestCase):
    def setUp(self):
        self.game_state = Mock()
        self.legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        self.state = State(self.game_state, self.legal_actions)

    def test_state_initialization(self):
        self.assertEqual(self.state.game_state, self.game_state)
        self.assertEqual(self.state.legal_actions, self.legal_actions)

    def test_represent_bird_deck(self):
        self.game_state.get_bird_deck.return_value.get_count.return_value = 10
        self.assertEqual(self.state._represent_bird_deck(), 10)

    def test_represent_discard_pile(self):
        self.game_state.get_discard_pile.return_value.get_count.return_value = 5
        self.assertEqual(self.state._represent_discard_pile(), 5)

    def test_represent_player_full(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = {'food': 3}
        player.get_game_board.return_value.to_representation.return_value = {'birds': ['bird1', 'bird2']}
        player.get_bird_hand.return_value.to_representation.return_value = {'cards': ['card1', 'card2']}
        representation = self.state._represent_player(player, full=True)
        self.assertEqual(representation, frozenset([('food_supply', {'food': 3}), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', {'cards': ['card1', 'card2']})]))

    def test_represent_player_partial(self):
        player = Mock()
        player.get_food_supply.return_value.to_representation.return_value = {'food': 3}
        player.get_game_board.return_value.to_representation.return_value = {'birds': ['bird1', 'bird2']}
        player.get_bird_hand.return_value.get_count.return_value = 2
        representation = self.state._represent_player(player, full=False)
        self.assertEqual(representation, frozenset([('food_supply', {'food': 3}), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)]))

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
        self.game_turn = 1
        self.num_turns = 10
        self.num_players = 2
        self.name = "test_player"

        player = self.state._construct_player(
            hand=self.hand,
            representation=self.representation,
            deck=self.deck,
            game_turn=self.game_turn,
            num_turns=self.num_turns,
            num_players=self.num_players,
            name=self.name
        )
        self.assertIsInstance(player, BotPlayer)
        self.assertEqual(player.name, self.name)
        self.assertEqual(player.hand, self.hand)
        self.assertEqual(player.food_supply.to_representation(), self.representation['food_supply'])
        self.assertEqual(player.game_board.to_representation(), self.representation['game_board'])

    def test_to_representation(self):
        self.game_state.get_num_turns.return_value = 10
        self.game_state.get_game_turn.return_value = 5
        self.game_state.get_phase.return_value = 'choose_action'
        self.state._represent_bird_deck.return_value = 20
        self.state._represent_discard_pile.return_value = 3
        self.game_state.tray.to_representation.return_value = frozenset([(1, 1,), (1, 2), (3, 1)])
        self.game_state.bird_feeder.to_representation.return_value = 5
        self.state._represent_player.return_value = frozenset([('food_supply', 3), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])
        self.state._get_opponents.return_value = ['opponent1', 'opponent2']
        representation = self.state.to_representation()
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
            ('discard_pile', 3),
            ('tray', frozenset([(1, 1,), (1, 2), (3, 1)])),
            ('bird_feeder', {'food_count': 5}),
            ('current_player', frozenset([('food_supply', {'food': 3}), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])),
            ('opponents', (frozenset([('food_supply', {'food': 3}), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)]), 
                           frozenset([('food_supply', {'food': 3}), ('game_board', frozenset([(0, 0), (0, 0)])), ('hand', 2)])
            ))
        ])
        self.game_state.get_num_turns.return_value = 10
        self.game_state.get_game_turn.return_value = 5
        self.game_state.get_phase.return_value = 'choose_action'
        self.state._represent_bird_deck.return_value = 20
        self.state._represent_discard_pile.return_value = 3
        self.game_state.tray.from_representation.return_value = 'tray'
        self.game_state.bird_feeder.from_representation.return_value = 'bird_feeder'
        self.state._construct_player.side_effect = ['current_player', 'opponent1', 'opponent2']
        game_state = self.state.from_representation(representation)
        self.assertEqual(game_state.num_turns, 10)
        self.assertEqual(game_state.game_turn, 5)
        self.assertEqual(game_state.phase, 'choose_action')
        self.assertEqual(game_state.bird_deck, 'valid_bird_deck')
        self.assertEqual(game_state.discard_pile, 'valid_discard_pile')
        self.assertEqual(game_state.tray, 'tray')
        self.assertEqual(game_state.bird_feeder, 'bird_feeder')
        self.assertEqual(game_state.players, ['current_player', 'opponent1', 'opponent2'])

class TestRandomPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RandomPolicy()

    def test_policy_choose_action_three_actions(self):
        legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        probabilities = self.policy._policy_choose_action(legal_actions)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_policy_choose_action_two_actions(self):
        legal_actions = ['play_a_bird', 'gain_food']
        probabilities = self.policy._policy_choose_action(legal_actions)
        self.assertEqual(probabilities, [1/2, 1/2])

    def test_policy_choose_a_bird_to_play(self):
        mock_hand = Mock()
        mock_hand.get_cards_in_hand.return_value = ['bird1', 'bird2', 'bird3']
        mock_food_supply = Mock()
        mock_food_supply.can_play_bird.side_effect = [True, False, True]
        probabilities = self.policy._policy_choose_a_bird_to_play(mock_hand, mock_food_supply)
        self.assertEqual(probabilities, [0.5, 0, 0.5])

    def test_policy_choose_a_bird_to_draw_deck_empty(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_deck = Mock()
        mock_deck.get_count.return_value = 0
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3, 0])

    def test_policy_choose_a_bird_to_draw_deck_not_empty(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_deck = Mock()
        mock_deck.get_count.return_value = 1
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/4, 1/4, 1/4, 1/4])

    def test_policy_choose_a_bird_to_draw_tray_partially_filled(self):
        mock_tray = Mock()
        mock_tray.get_count.return_value = 2
        mock_deck = Mock()
        mock_deck.get_count.return_value = 1
        probabilities = self.policy._policy_choose_a_bird_to_draw(mock_tray, mock_deck)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_call_choose_action(self):
        mock_state = Mock()
        mock_state.phase = 'choose_action'
        mock_state.legal_actions = ['play_a_bird', 'gain_food', 'draw_a_card']
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [1/3, 1/3, 1/3])

    def test_call_choose_a_bird_to_play(self):
        mock_state = Mock()
        mock_state.phase = 'choose_a_bird_to_play'
        mock_state.bird_hand = Mock()
        mock_state.bird_hand.get_cards_in_hand.return_value = ['bird1', 'bird2', 'bird3']
        mock_state.food_supply = Mock()
        mock_state.food_supply.can_play_bird.side_effect = [True, False, True]
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [0.5, 0, 0.5])

    def test_call_choose_a_bird_to_draw(self):
        mock_state = Mock()
        mock_state.phase = 'choose_a_bird_to_draw'
        mock_state.tray = Mock()
        mock_state.tray.get_count.return_value = 3
        mock_state.bird_deck = Mock()
        mock_state.bird_deck.get_count.return_value = 1
        probabilities = self.policy(mock_state)
        self.assertEqual(probabilities, [1/4, 1/4, 1/4, 1/4])

if __name__ == '__main__':
    unittest.main()