import unittest
from src.entities.gameboard import GameBoard
from io import StringIO
from unittest.mock import patch

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
        expected_output = "{:<30s}{:<15s}{:<10s}".format("Bird Name", "Point Value", "Food Cost") + "\n"
        for _ in range(5):
            expected_output += "{:<30s}{:<15s}{:<10s}".format("empty", "--", "--") + "\n"

        with patch('sys.stdout', new=StringIO()) as fake_output:
            self.gameboard.render()
            self.assertEqual(fake_output.getvalue().strip(), expected_output.strip()) # Use strip() to remove trailing newline

    if __name__ == '__main__':
        unittest.main()
