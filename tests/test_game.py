import unittest
from src.game import WingspanGame
from data.bird_list import birds as bird_list

class TestWingspanGame(unittest.TestCase):
    def setUp(self):
        self.game = WingspanGame()

    def test_setup(self):
        num_players = 2
        num_turns = 5
        num_starting_cards = 3
        self.game.setup(num_turns, num_players, num_starting_cards)
        # Assertions to test the setup of the game object
        self.assertEqual(self.game.game_state.num_players, num_players)
        self.assertEqual(self.game.game_state.num_turns, num_turns)
        self.assertEqual(self.game.bird_feeder.food_count, 5)
        self.assertEqual(len(self.game.tray.see_birds_in_tray()), 3)
        self.assertEqual(len(self.game.bird_hands[0].get_cards_in_hand()), 3)
        self.assertEqual(len(self.game.bird_hands[1].get_cards_in_hand()), 3)
        self.assertEqual([supply.amount for supply in self.game.food_supplies], [2] * num_players)
        
        cards_left_in_deck = len(bird_list) - num_players * num_starting_cards - 3
        self.assertEqual(self.game.bird_deck.get_count(), cards_left_in_deck)
        
if __name__ == "__main__":
    unittest.main()