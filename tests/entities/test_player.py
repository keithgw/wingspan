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
from unittest.mock import patch, Mock, call

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

    @patch.object(Player, '_enumerate_legal_actions', return_value=['action1', 'action2'])
    @patch.object(Player, '_choose_action', return_value='action1')
    def test_request_action(self, mock_choose_action, mock_enumerate_legal_actions):
        # Create mocks
        mock_game_state = Mock(spec=GameState)
        mock_tray = Mock()
        mock_tray.get_count.return_value = 3
        mock_bird_deck = Mock()
        mock_bird_deck.get_count.return_value = 1
        mock_game_state.get_tray.return_value = mock_tray
        mock_game_state.get_bird_deck.return_value = mock_bird_deck
        player = Player(name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

        # call request_action
        action = player.request_action(game_state=mock_game_state)

        # check that _enumerate_legal_actions and _choose_action were called with the correct arguments
        mock_enumerate_legal_actions.assert_called_once_with(tray=mock_tray, bird_deck=mock_bird_deck)
        mock_choose_action.assert_called_once_with(legal_actions=['action1', 'action2'], game_state=mock_game_state)

        # assert that the action returned by request_action is the same as the action returned by _choose_action
        self.assertEqual(action, 'action1')

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

    @patch.object(Player, '_enumerate_playable_birds', return_value=['bird1', 'bird2'])
    @patch.object(Player, '_choose_a_bird_to_play', return_value='bird1')
    def test_play_a_bird(self, mock_choose_a_bird_to_play, mock_enumerate_playable_birds):
        # Create mocks
        mock_game_state = Mock(spec=GameState)
        mock_bird_card = Mock()
        mock_bird_card.get_food_cost.return_value = 1
        mock_bird_hand = Mock()
        mock_bird_hand.get_card.return_value = mock_bird_card
        mock_food_supply = Mock()
        mock_game_board = Mock()
        player = Player(
            name=self.name, 
            bird_hand=mock_bird_hand, 
            food_supply=mock_food_supply, 
            num_turns=self.num_turns, 
            game_board=mock_game_board
            )
        
        # call play_a_bird
        player.play_a_bird(game_state=mock_game_state)

        # check that _enumerate_playable_birds and _choose_a_bird_to_play were called with the correct arguments
        mock_enumerate_playable_birds.assert_called_once()
        mock_choose_a_bird_to_play.assert_called_once_with(playable_birds=['bird1', 'bird2'], game_state=mock_game_state)

        # check that food cost was decremented
        mock_food_supply.decrement.assert_called_once_with(1)

        # check that the bird was added to the game board
        mock_bird_hand.play_bird.assert_called_once_with(bird_name='bird1', game_board=mock_game_board)

    def test_gain_food(self):
        bird_feeder = BirdFeeder()
        bird_feeder.reroll()
        self.player.gain_food(bird_feeder)
        
        # Check if the player's food supply was incremented by 1
        self.assertEqual(self.player.food_supply.amount, 3)

        # Check that the food came from the bird feeder
        self.assertEqual(bird_feeder.food_count, 4)

    @patch.object(Player, '_choose_a_bird_to_draw', return_value='bird1')
    def test_draw_a_bird_empty_deck(self, mock_choose_a_bird_to_draw):
        # Create mocks
        mock_game_state = Mock(spec=GameState)
        mock_tray = Mock()
        mock_tray.see_birds_in_tray.return_value = ['bird1', 'bird2']
        mock_bird_deck = Mock()
        mock_bird_deck.get_count.return_value = 0
        mock_game_state.get_tray.return_value = mock_tray
        mock_game_state.get_bird_deck.return_value = mock_bird_deck
        mock_hand = Mock()
        mock_hand.draw_bird_from_tray.return_value = None
        player = Player(name=self.name, bird_hand=mock_hand, food_supply=self.food_supply, num_turns=self.num_turns)

        # call draw_a_bird
        player.draw_a_bird(game_state=mock_game_state)

        # check that _choose_a_bird_to_draw was called with the correct arguments
        mock_choose_a_bird_to_draw.assert_called_once_with(valid_choices=['bird1', 'bird2'], game_state=mock_game_state)

        # check that a bird was drawn from the tray
        mock_hand.draw_bird_from_tray.assert_called_once_with(tray=mock_tray, bird_name='bird1')

    @patch.object(Player, '_choose_a_bird_to_draw', return_value='deck')
    def test_draw_a_bird_from_deck(self, mock_choose_a_bird_to_draw):
        # Create mocks
        mock_game_state = Mock(spec=GameState)
        mock_tray = Mock()
        mock_tray.see_birds_in_tray.return_value = ['bird1', 'bird2']
        mock_bird_deck = Mock()
        mock_bird_deck.get_count.return_value = 1
        mock_game_state.get_tray.return_value = mock_tray
        mock_game_state.get_bird_deck.return_value = mock_bird_deck
        mock_hand = Mock()
        mock_hand.draw_card_from_deck.return_value = None
        mock_hand.get_card_names_in_hand.return_value = ['original_bird', 'new_bird']
        player = Player(name=self.name, bird_hand=mock_hand, food_supply=self.food_supply, num_turns=self.num_turns)

        # call draw_a_bird
        player.draw_a_bird(game_state=mock_game_state)

        # check that _choose_a_bird_to_draw was called with the correct arguments
        mock_choose_a_bird_to_draw.assert_called_once_with(valid_choices=['bird1', 'bird2', 'deck'], game_state=mock_game_state)

        # check that a bird was drawn from the tray
        mock_hand.draw_card_from_deck.assert_called_once_with(mock_bird_deck)


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
        self.mock_game_state = Mock(spec=GameState)

    @patch('builtins.input', return_value='1')
    def test_choose_action(self, input):
        # An input of 1 should return 'play_a_bird'
        legal_actions = ['play_a_bird', 'gain_food', 'draw_a_bird']
        action = self.player._choose_action(legal_actions=legal_actions, game_state=self.mock_game_state)
        self.assertEqual(action, 'play_a_bird')

    @patch('builtins.input', return_value='Osprey')
    def test_choose_a_bird_to_play(self, input):
        # An input of 'Osprey' should return the Osprey bird, which should be playable, since its both in the hand and the player has sufficient food
        valid_bird = self.birds[0].get_name()
        bird = self.player._choose_a_bird_to_play(playable_birds=[valid_bird], game_state=self.mock_game_state)
        self.assertEqual(bird, valid_bird)

    @patch('builtins.input', return_value='deck')
    def test__choose_a_bird_to_draw(self, input):
        # An input of 'deck' should return 'deck'
        choice = self.player._choose_a_bird_to_draw(valid_choices=['deck'], game_state=self.mock_game_state)
        self.assertEqual(choice, 'deck')

class TestBotPlayer(TestPlayerBase):
    def test_choose_action(self):
       # Create a mock policy that returns a fixed action
        mock_policy = Mock()
        mock_policy.return_value = 'mock_action'

        # Create a player with the mock policy
        player = BotPlayer(policy=mock_policy, name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

        # Create a mock game state
        mock_game_state = Mock(spec=GameState)

        # Call the method with a list of legal actions
        legal_actions = ['action1', 'action2', 'mock_action']
        result = player._choose_action(legal_actions, mock_game_state)

        # Check that the policy was called with the correct arguments
        mock_policy.assert_called_once_with(state=mock_game_state, actions=legal_actions)

        # Check that the result is the action returned by the policy
        self.assertEqual(result, 'mock_action')

    def test_choose_a_bird_to_play(self):
       # Create a mock policy that returns a fixed bird
        mock_policy = Mock()
        mock_policy.return_value = 'mock_bird'

        # Create a player with the mock policy
        player = BotPlayer(policy=mock_policy, name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)

        # Create a mock game state
        mock_game_state = Mock(spec=GameState)

        # Call the method with a list of playable birds
        playable_birds = ['bird1', 'bird2', 'mock_bird']
        result = player._choose_a_bird_to_play(playable_birds=playable_birds, game_state=mock_game_state)

        # Check that the policy was called with the correct arguments
        mock_policy.assert_called_once_with(state=mock_game_state, actions=playable_birds)

        # Check that the result is the action returned by the policy
        self.assertEqual(result, 'mock_bird')

    def test__choose_a_bird_to_draw(self):
         # Create a mock policy that returns a fixed bird
          mock_policy = Mock()
          mock_policy.return_value = 'mock_bird'
    
          # Create a player with the mock policy
          player = BotPlayer(policy=mock_policy, name=self.name, bird_hand=self.bird_hand, food_supply=self.food_supply, num_turns=self.num_turns)
    
          # Create a mock game state
          mock_game_state = Mock(spec=GameState)
    
          # Call the method with a list of valid choices
          valid_choices = ['bird1', 'bird2', 'mock_bird']
          result = player._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=mock_game_state)
    
          # Check that the policy was called with the correct arguments
          mock_policy.assert_called_once_with(state=mock_game_state, actions=valid_choices)
    
          # Check that the result is the action returned by the policy
          self.assertEqual(result, 'mock_bird')

        
if __name__ == '__main__':
    unittest.main()
