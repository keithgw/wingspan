import unittest
from src.entities.hand import BirdHand
from src.entities.bird import Bird
from src.entities.food_supply import FoodSupply
from src.entities.player import Player
from src.entities.game_state import GameState
from src.entities.birdfeeder import BirdFeeder
from src.entities.tray import Tray
from src.entities.deck import Deck
from src.entities.gameboard import GameBoard
from unittest.mock import patch

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.bird_hand = BirdHand()
        self.birds = [Bird('Osprey', 5, 1), Bird('Bald Eagle', 9, 3), Bird('Peregrine Falcon', 5, 2)]
        for bird in self.birds:
            self.bird_hand.add_card(bird, bird.get_name())
        self.food_supply = FoodSupply(2)
        self.actions = ['play_a_bird', 'gain_food', 'draw_a_bird']
        self.player = Player(self.bird_hand, self.food_supply, self.actions)
        self.game_state = GameState(num_turns=3, num_players=1)
        self.tray = Tray()
        self.bird_deck = Deck(cards = [Bird('Anhinga', 6, 2), Bird('Barred Owl', 3, 1), Bird('Willet', 4, 1), Bird('Carolina Chickadee', 2, 1)])

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

    @patch('builtins.input', return_value=1)
    @patch.object(Player, '_enumerate_legal_actions', return_value=['play_a_bird', 'gain_food', 'draw_a_bird'])
    def test_choose_action(self, input, enumerate_legal_actions_mock):
        # An input of 1 should return 'play_a_bird'
        action = self.player._choose_action(self.tray, self.bird_deck)
        self.assertEqual(action, 'play_a_bird')

        # Check if _enumerate_legal_actions was called once
        enumerate_legal_actions_mock.assert_called_once() 

    @patch.object(Player, '_choose_action', return_value='play_a_bird')
    def test_request_action(self, choose_action_mock):
        player = Player(None, None, None)
        action = player.request_action(None, None)
        
        # Check if choose_action was called once
        choose_action_mock.assert_called_once()

        # Check if the returned action is the same as the action returned by choose_action
        self.assertEqual(action, 'play_a_bird')

    @patch('builtins.input', return_value='Osprey')
    def test_choose_a_bird(self, input):
        # An input of 'Osprey' should return the Osprey bird, which should be playable, since its both in the hand and the player has sufficient food
        valid_bird = self.birds[0].get_name()
        bird = self.player.choose_a_bird()
        self.assertEqual(bird, valid_bird)

    def test_play_a_bird(self):
        bird = self.birds[0]
        initial_food_supply = self.player.food_supply.amount
        final_food_supply = initial_food_supply - bird.get_food_cost()
        self.player.play_a_bird(bird.get_name())

        # Check if the bird was removed from the player's hand
        self.assertNotIn(bird, self.player.bird_hand.get_cards_in_hand())

        # Check if the bird was added to the game board
        self.assertIn(bird, self.player.game_board.get_birds())

        # Check if the player's food supply was decremented by the bird's food cost
        food_cost = bird.get_food_cost()
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
    def test_draw_bird(self, input):

        # empty tray, cards in deck
        self.player.draw_bird(self.bird_deck, self.tray)
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
        self.player.draw_bird(self.bird_deck, self.tray)
        self.assertIn('Anhinga', self.player.bird_hand.get_card_names_in_hand())

if __name__ == '__main__':
    unittest.main()
