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
        self.game.setup(num_players, num_turns, num_starting_cards)
        # Assertions to test the setup of the game object
        self.assertEqual(self.game.num_players, num_players)
        self.assertEqual(self.game.num_turns, num_turns)
        self.assertEqual(self.game.num_starting_cards, num_starting_cards)
        self.assertEqual(self.game.bird_feeder.food_count, 5)
        self.assertEqual(len(self.game.tray.get_birds_in_tray()), 3)
        self.assertEqual(len(self.game.game_state.get_player_bird_hand(0).get_cards()), 3)
        self.assertEqual(len(self.game.game_state.get_player_bird_hand(1).get_cards()), 3)
        self.assertEqual(self.game.food_supplies, [2] * num_players)
        
        cards_left_in_deck = len(bird_list) - num_players * num_starting_cards - 3
        self.assertEqual(self.game.bird_deck.get_count(), cards_left_in_deck)
        
if __name__ == "__main__":
    unittest.main()
