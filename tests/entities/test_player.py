import unittest
from src.entities.hand import BirdHand
from src.entities.bird import Bird
from src.entities.food_supply import FoodSupply
from src.entities.player import Player, HumanPlayer, BotPlayer
from src.entities.game_state import GameState
from src.entities.birdfeeder import BirdFeeder
from src.entities.tray import Tray
from src.entities.deck import Deck
from src.entities.gameboard import GameBoard
from unittest.mock import patch, Mock

class TestPlayerBase(unittest.TestCase):
    def setUp(self):
            self.name = "Test Player"
            self.num_turns = 5
            self.bird_hand = BirdHand()
            self.birds = [Bird('Osprey', 5, 1), Bird('Bald Eagle', 9, 3), Bird('Peregrine Falcon', 5, 2)]
            for bird in self.birds:
                self.bird_hand.add_card(bird, bird.get_name())
            self.food_supply = FoodSupply(2)
            self.tray = Tray()
            self.bird_deck = Deck(cards = [Bird('Anhinga', 6, 2), Bird('Barred Owl', 3, 1), Bird('Willet', 4, 1), Bird('Carolina Chickadee', 2, 1)])

class TestPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.player = Player(name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

    def test_get_name(self):
        name = self.player.get_name()
        self.assertEqual(name, "Test Player")

    def test_set_name(self):
        self.player.set_name("New Name")
        name = self.player.get_name()
        self.assertEqual(name, "New Name")

    def test_get_bird_hand(self):
        bird_hand = self.player.get_bird_hand()
        self.assertEqual(bird_hand, self.bird_hand)

    def test_get_food_supply(self):
        food_supply = self.player.get_food_supply()
        self.assertEqual(food_supply, self.food_supply)

    def test_get_game_board(self):
        game_board = GameBoard()
        self.player.game_board = game_board
        self.assertEqual(self.player.get_game_board(), game_board)

    def test_enumerate_legal_actions(self):
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)
        
        # Player should be able to play a bird, since they have birds in their hand and sufficient food to play at least one
        self.assertIn('play_a_bird', legal_actions)

        # Player cannot play a bird, insufficient food
        self.player.food_supply.decrement(2)
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)
        self.assertNotIn('play_a_bird', legal_actions)

        # Player cannot play a bird, no birds in hand
        self.player.food_supply.increment(2)
        self.player.bird_hand = BirdHand()
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)
        self.assertNotIn('play_a_bird', legal_actions)

        # Player should always be able to gain food
        self.assertIn('gain_food', legal_actions)

        # Player should be able to draw a bird, since there are birds in the bird deck, but not in the tray
        self.assertIn('draw_a_bird', legal_actions)

        # Player should be able to draw a bird, since there are birds in the tray, but not in the bird deck
        discard_pile = Deck()
        self.tray.flush(discard_pile=discard_pile, bird_deck=self.bird_deck)
        empty_deck = Deck()
        legal_actions = self.player._enumerate_legal_actions(self.tray, empty_deck)
        self.assertIn('draw_a_bird', legal_actions)

        # Player should be able to draw a bird, since there are birds in the bird deck and in the tray
        legal_actions = self.player._enumerate_legal_actions(self.tray, self.bird_deck)

        # Player cannot draw a bird, no birds in bird deck or tray
        empty_tray = Tray()
        legal_actions = self.player._enumerate_legal_actions(empty_tray, empty_deck)
        self.assertNotIn('draw_a_bird', legal_actions)

    @patch.object(Player, '_choose_action', return_value='play_a_bird')
    def test_request_action(self, choose_action_mock):
        player = Player(None, None, None, None)
        action = player.request_action(None)
        
        # Check if choose_action was called once
        choose_action_mock.assert_called_once()

        # Check if the returned action is the same as the action returned by choose_action
        self.assertEqual(action, 'play_a_bird')

    def test_take_action(self):
        # test that an error is raised if action is not valid
        with self.assertRaises(Exception):
            self.player.take_action(action='invalid_action', game_state=None)
        
        # test that play_a_bird is called if action == "play_a_bird"
        with patch.object(Player, 'play_a_bird') as play_a_bird_mock:
            self.player.take_action(action='play_a_bird', game_state=None)
            play_a_bird_mock.assert_called_once()

        # test that gain_food is called if action == "gain_food"
        with patch.object(Player, 'gain_food') as gain_food_mock:
            mock_game_state = Mock()
            mock_game_state.get_bird_feeder.return_value = None
            self.player.take_action(action='gain_food', game_state=mock_game_state)
            gain_food_mock.assert_called_once()

        # test that draw_a_bird is called if action == "draw_a_bird"
        with patch.object(Player, 'draw_a_bird') as draw_bird_mock:
            mock_game_state = Mock()
            mock_game_state.get_tray.return_value = None
            mock_game_state.get_bird_deck.return_value = None
            self.player.take_action(action='draw_a_bird', game_state=mock_game_state)
            draw_bird_mock.assert_called_once()

    def test_play_a_bird(self):
        bird = self.birds[0]
        bird_name = bird.get_name()
        initial_food_supply = self.player.food_supply.amount
        final_food_supply = initial_food_supply - bird.get_food_cost()
        with patch.object(self.player, '_choose_a_bird_to_play', return_value=bird_name):
            self.player.play_a_bird()

        # Check if the bird was removed from the player's hand
        self.assertNotIn(bird, self.player.bird_hand.get_cards_in_hand())

        # Check if the bird was added to the game board
        self.assertIn(bird, self.player.game_board.get_birds())

        # Check if the player's food supply was decremented by the bird's food cost
        self.assertEqual(self.player.food_supply.amount, final_food_supply)

    def test_gain_food(self):
        bird_feeder = BirdFeeder()
        bird_feeder.reroll()
        self.player.gain_food(bird_feeder)
        
        # Check if the player's food supply was incremented by 1
        self.assertEqual(self.player.food_supply.amount, 3)

        # Check that the food came from the bird feeder
        self.assertEqual(bird_feeder.food_count, 4)

    @patch('builtins.input', return_value='deck')
    def test_draw_a_bird(self, input):
        with patch.object(self.player, '_choose_a_bird_to_draw', return_value='deck'):
            # empty tray, empty deck
            self.player.draw_a_bird(self.tray, self.bird_deck)
            # Top card in deck should be in player's hand
            self.assertIn('Anhinga', self.player.bird_hand.get_card_names_in_hand())

        # cards in tray, cards in deck
        # put the card back in the deck, goes to the bottom)
        anhinga = self.player.bird_hand.discard_card('Anhinga')
        self.bird_deck.add_card(anhinga)
        discard_pile = Deck()
        # top 3 cards in deck should be in tray
        self.tray.flush(discard_pile=discard_pile, bird_deck=self.bird_deck)
        # this should return 'deck', and Anhinga is the only card left in the deck
        with patch.object(self.player, '_choose_a_bird_to_draw', return_value='deck'):
            self.player.draw_a_bird(self.tray, self.bird_deck)
            self.assertIn('Anhinga', self.player.bird_hand.get_card_names_in_hand())

    def test_end_turn(self):
        # Check that the player's turn count is decremented by 1
        initial_turns_remaining = self.player.get_turns_remaining()
        self.player.end_turn()
        self.assertEqual(self.player.turns_remaining, initial_turns_remaining - 1)

        # Check that the player's score is updated
        self.player.game_board.add_bird(self.birds[0])
        self.player.end_turn()
        self.assertEqual(self.player.score, self.birds[0].get_points())

    def get_turns_remaining(self):
        self.assertEqual(self.player.get_turns_remaining(), self.player.turns_remaining)

class TestHumanPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        self.player = HumanPlayer(name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

    @patch('builtins.input', return_value='1')
    @patch.object(Player, '_enumerate_legal_actions', return_value=['play_a_bird', 'gain_food', 'draw_a_bird'])
    def test__choose_action(self, input, enumerate_legal_actions_mock):
        # An input of 1 should return 'play_a_bird'
        mock_game_state = Mock()
        action = self.player._choose_action(game_state=mock_game_state)
        self.assertEqual(action, 'play_a_bird')

        # Check if _enumerate_legal_actions was called once
        enumerate_legal_actions_mock.assert_called_once() 

    @patch('builtins.input', return_value='Osprey')
    def test__choose_a_bird_to_play(self, input):
        # An input of 'Osprey' should return the Osprey bird, which should be playable, since its both in the hand and the player has sufficient food
        valid_bird = self.birds[0].get_name()
        bird = self.player._choose_a_bird_to_play()
        self.assertEqual(bird, valid_bird)

    @patch('builtins.input', return_value='deck')
    def test__choose_a_bird_to_draw(self, input):
        # An input of 'deck' should return 'deck'
        choice = self.player._choose_a_bird_to_draw(bird_deck=self.bird_deck, tray=self.tray)
        self.assertEqual(choice, 'deck')

class TestBotPlayer(TestPlayerBase):
    def setUp(self):
        super().setUp()
        mock_policy = Mock()
        mock_policy.return_value = [0.1, 0.2, 0.7]
        self.test_player = BotPlayer(policy=mock_policy, name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

    @patch('numpy.random.choice')
    def test__choose_action(self, mock_np_choice):
        # Create a mock GameState object
        mock_game_state = Mock()
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_game_state.get_tray.return_value = mock_tray

        mock_bird_deck = Mock()
        mock_bird_deck.get_count.return_value = 3
        mock_game_state.get_bird_deck.return_value = mock_bird_deck

        # Mock numpy's random choice to return a predictable result
        mock_np_choice.return_value = 2

        # Create a mock _enumerate_legal_actions method
        mock_enumerate_legal_actions = Mock()
        mock_enumerate_legal_actions.return_value = ['action1', 'action2', 'action3']

        # Set it as the _enumerate_legal_actions method of self.test_player
        self.test_player._enumerate_legal_actions = mock_enumerate_legal_actions

        # Create a mock _get_state method
        mock_get_state = Mock()
        mock_get_state.return_value = 'mock_state'

        # Set it as the _get_state method of self.test_player
        self.test_player._get_state = mock_get_state

        # Call the method to test
        action = self.test_player._choose_action(mock_game_state)

        # Check if the methods were called correctly
        mock_game_state.get_tray.assert_called_once()
        mock_game_state.get_bird_deck.assert_called_once()
        self.test_player._enumerate_legal_actions.assert_called_once_with(tray=mock_tray, bird_deck=mock_bird_deck)
        self.test_player._get_state.assert_called_once_with(phase='choose_action', tray=mock_tray, bird_deck=mock_bird_deck, legal_actions=['action1', 'action2', 'action3'])
        self.test_player.policy.assert_called_once_with('mock_state')
        mock_np_choice.assert_called_once_with(len([0.1, 0.2, 0.7]), p=[0.1, 0.2, 0.7])

        # Check if the returned action is correct
        self.assertEqual(action, 'action3')

    @patch('numpy.random.choice')
    def test__choose_a_bird_to_play(self, mock_np_choice):
        # Create mock methods
        mock_get_state = Mock()
        mock_get_state.return_value = 'mock_state'
        mock_get_card_names_in_hand = Mock()
        mock_get_card_names_in_hand.return_value = ['bird1', 'bird2', 'bird3']

        # Set them as the methods of self.test_player
        self.test_player._get_state = mock_get_state
        self.test_player.bird_hand.get_card_names_in_hand = mock_get_card_names_in_hand

        # Mock numpy's random choice to return a predictable result
        mock_np_choice.return_value = 1

        # Call the method to test
        chosen_bird = self.test_player._choose_a_bird_to_play()

        # Check if the methods were called correctly
        self.test_player._get_state.assert_called_once_with(phase='choose_a_bird_to_play')
        self.test_player.bird_hand.get_card_names_in_hand.assert_called_once()
        self.test_player.policy.assert_called_once_with('mock_state')
        mock_np_choice.assert_called_once_with(len(['bird1', 'bird2', 'bird3']), p=[0.1, 0.2, 0.7])

        # Check if the returned bird is correct
        self.assertEqual(chosen_bird, 'bird2')

    @patch('numpy.random.choice')
    def test__choose_a_bird_to_draw(self, mock_np_choice):
        # Create a mock tray and deck
        mock_tray = Mock(spec=Tray)
        mock_tray.see_birds_in_tray.return_value = ['bird1', 'bird2', 'bird3']
        mock_deck = Mock(speck=Deck)
        
        # Create mock methods
        mock_get_state = Mock()
        mock_get_state.return_value = 'mock_state'

        # Set them as the methods of self.test_player
        self.test_player._get_state = mock_get_state

        # Mock numpy's random choice to return a predictable result
        mock_np_choice.return_value = 1

        # Call the method to test
        chosen_bird = self.test_player._choose_a_bird_to_draw(tray=mock_tray, bird_deck=mock_deck)

        # Check if the methods were called correctly
        self.test_player._get_state.assert_called_once_with(phase='choose_a_bird_to_draw', tray=mock_tray, bird_deck=mock_deck)
        self.test_player.policy.assert_called_once_with('mock_state')
        mock_np_choice.assert_called_once_with(len([0.1, 0.2, 0.7]), p=[0.1, 0.2, 0.7])

        # Check if the returned bird is correct
        self.assertEqual(chosen_bird, 'bird2')
        
if __name__ == '__main__':
    unittest.main()
