import unittest
from src.entities.gameboard import GameBoard
from unittest.mock import patch
from src.utilities.utils import render_bird_container

class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.gameboard = GameBoard()
        self.mock_card = "Osprey"

    def test_check_if_full(self):
        self.assertFalse(self.gameboard.check_if_full())
        for _ in range(5):
            self.gameboard.add_card(self.mock_card)
        self.assertTrue(self.gameboard.check_if_full())

    def test_add_card(self):
        self.gameboard.add_card(self.mock_card)
        cards = self.gameboard.get_birds()
        self.assertIn(self.mock_card, cards)

    def test_get_birds(self):
        self.gameboard.add_card(self.mock_card)
        cards = self.gameboard.get_birds()
        self.assertEqual([self.mock_card], cards)

def test_render(self):
    self.gameboard.add_card(self.mock_card)
    
    with patch('src.utils.render_bird_container', return_value="Mocked render output") as mock_render:
        self.gameboard.render()
        mock_render.assert_called_once_with(self.gameboard.get_birds(), self.gameboard.limit)

    if __name__ == '__main__':
        unittest.main()
