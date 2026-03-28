import unittest
from io import StringIO
from unittest.mock import patch

from src.entities.bird import Bird
from src.entities.deck import Deck
from src.entities.gameboard import GameBoard


class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.gameboard = GameBoard()
        self.mock_card = Bird("Osprey", 5, 1)

    def test_check_if_full(self):
        self.assertFalse(self.gameboard.check_if_full())
        for _ in range(5):
            self.gameboard.add_bird(self.mock_card)
        self.assertTrue(self.gameboard.check_if_full())

    def test_add_bird(self):
        self.gameboard.add_bird(self.mock_card)
        cards = self.gameboard.get_birds()
        self.assertIn(self.mock_card, cards)

    def test_get_birds(self):
        self.gameboard.add_bird(self.mock_card)
        cards = self.gameboard.get_birds()
        self.assertEqual([self.mock_card], cards)

    def test_render(self):
        # check that render calls render_bird_container, and prints the returned value
        with (
            patch(
                "src.entities.gameboard.render_bird_container",
                return_value="Mocked render output",
            ) as mock_render,
            patch("sys.stdout", new=StringIO()) as mock_stdout,
        ):
            self.gameboard.render()
            self.assertEqual(mock_stdout.getvalue().strip(), "Mocked render output")
            mock_render.assert_called_once_with(
                bird_container=self.gameboard.get_birds(),
                capacity=self.gameboard.capacity,
            )

    def test_get_score(self):
        # check that get_score returns the sum of the scores of the birds on the game board
        self.gameboard.add_bird(self.mock_card)
        self.assertEqual(self.gameboard.get_score(), self.mock_card.get_points())

    def test_to_representation_full(self):
        for _ in range(5):
            self.gameboard.add_bird(Bird("Osprey", 5, 1))
        rep = self.gameboard.to_representation()
        self.assertEqual(len(rep), 5)
        self.assertEqual(rep, ((5, 1),) * 5)

    def test_to_representation_partial(self):
        self.gameboard.add_bird(Bird("Osprey", 5, 1))
        rep = self.gameboard.to_representation()
        self.assertEqual(len(rep), 5)
        self.assertEqual(rep, ((0, 0), (0, 0), (0, 0), (0, 0), (5, 1)))

    def test_from_representation(self):
        deck = Deck()
        deck.add_card(Bird("Osprey", 5, 1))
        deck.add_card(Bird("Cardinal", 3, 2))
        rep = ((0, 0), (0, 0), (0, 0), (0, 0), (5, 1))
        board = GameBoard.from_representation(rep, deck)
        self.assertEqual(len(board.get_birds()), 1)
        self.assertEqual(board.capacity, 5)
        self.assertEqual(deck.get_count(), 1)


if __name__ == "__main__":
    unittest.main()
