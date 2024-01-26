import unittest
from src.entities.gameboard import GameBoard
from src.entities.bird import Bird
from src.entities.deck import Deck
from unittest.mock import patch
from io import StringIO

class TestGameBoard(unittest.TestCase):
    def setUp(self):
        self.gameboard = GameBoard()
        self.mock_card = Bird("Osprey", 5, 1)

    def test_check_if_full(self):
        self.assertFalse(self.gameboard.check_if_full())
        for _ in range(self.gameboard.capacity):
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
        with patch('src.entities.gameboard.render_bird_container', return_value="Mocked render output") as mock_render, \
            patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.gameboard.render()
            self.assertEqual(mock_stdout.getvalue().strip(), "Mocked render output")
            mock_render.assert_called_once_with(bird_container=self.gameboard.get_birds(), capacity=self.gameboard.capacity)

    def test_get_score(self):
        # check that get_score returns the sum of the scores of the birds on the game board
        self.gameboard.add_bird(self.mock_card)
        self.assertEqual(self.gameboard.get_score(), self.mock_card.get_points())

    def test_to_representation_full_board(self):
        # check that to_representation returns the representation of the game board
        for _ in range(self.gameboard.capacity):
            self.gameboard.add_bird(self.mock_card)
        self.assertEqual(self.gameboard.to_representation(), frozenset([self.mock_card.to_representation()] * self.gameboard.capacity))

    def test_to_representation_partially_full_board(self):
        # check that to_representation returns the representation of the game board
        for _ in range(self.gameboard.capacity - 1):
            self.gameboard.add_bird(self.mock_card)

        board_rep = [self.mock_card.to_representation()] * (self.gameboard.capacity - 1)
        placeholder_rep = [Bird("Placeholder", 0, 0).to_representation()]
        self.assertEqual(self.gameboard.to_representation(), frozenset(board_rep + placeholder_rep)) 

    def test_from_representation(self):
        # create a mock representation
        representation = frozenset([(1, 2), (3, 4), (0, 0)])

        # create a mock deck
        deck = Deck()
        deck.add_bird(Bird("Bird 1", 1, 2))
        deck.add_bird(Bird("Bird 2", 2, 2))
        deck.add_bird(Bird("Bird 3", 3, 4))

        # call the method under test
        gameboard = GameBoard.from_representation(representation, deck)

        # assert the gameboard state
        self.assertEqual(gameboard.capacity, 3)
        self.assertEqual(len(gameboard.get_birds()), 2)
        self.assertIn(Bird("Bird 1", 1, 2), gameboard.get_birds())
        self.assertIn(Bird("Bird 3", 3, 4), gameboard.get_birds())

if __name__ == '__main__':
    unittest.main()