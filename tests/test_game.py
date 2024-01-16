import unittest
from src.game import WingspanGame
from data.bird_list import birds as bird_list

class TestWingspanGame(unittest.TestCase):
    def setUp(self):
        self.num_players = 2
        self.num_turns = 5
        self.num_starting_cards = 3
        self.game = WingspanGame()
        self.game.setup(self.num_turns, self.num_players, self.num_starting_cards)

    num_players = 2
    num_turns = 5
    num_starting_cards = 3

    def test_setup(self):
        # Assertions to test the setup of the game object
        self.assertEqual(self.game.game_state.num_players, self.num_players)
        self.assertEqual(self.game.game_state.num_turns, self.num_turns)
        self.assertEqual(self.game.bird_feeder.food_count, 5)
        self.assertEqual(len(self.game.tray.see_birds_in_tray()), 3)
        self.assertEqual(len(self.game.players), self.num_players)
        self.assertEqual(len(self.game.players[0].bird_hand.get_cards_in_hand()), 3)
        self.assertEqual(len(self.game.players[1].bird_hand.get_cards_in_hand()), 3)
        food_supplies = [player.food_supply.amount for player in self.game.players]
        self.assertEqual(food_supplies, [2] * self.num_players)
        
        cards_left_in_deck = len(bird_list) - self.num_players * self.num_starting_cards - 3
        self.assertEqual(self.game.bird_deck.get_count(), cards_left_in_deck)
        self.assertEqual(self.game.discard_pile.get_count(), 0)

    def test_get_player_scores(self):
        # Assertions to test the scoring of the game object
        self.assertEqual(self.game.get_player_scores(), [0] * self.num_players)

    def test_determine_winners_there_is_a_tie(self):
        # Assertions to test the determination of winners
        self.assertEqual(self.game.determine_winners(), [0, 1])

    def test_determine_winners_there_is_a_winner(self):
        # Assertions to test the determination of winners
        self.game.players[0].score = 100
        self.assertEqual(self.game.determine_winners(), [0])
        
if __name__ == "__main__":
    unittest.main()