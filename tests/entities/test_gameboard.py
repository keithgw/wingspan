import unittest
from src.entities.gameboard import GameBoard

class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.gameboard = GameBoard()
        self.mock_card = "Osprey"

    def test_add_card(self):
        self.gameboard.add_card(self.mock_card)
        cards = self.gameboard.get_cards()
        self.assertIn(self.mock_card, cards)

    def test_get_cards(self):
        self.gameboard.add_card(self.mock_card)
        cards = self.gameboard.get_cards()
        self.assertEqual([self.mock_card], cards)

if __name__ == '__main__':
    unittest.main()
