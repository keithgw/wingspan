import unittest
from src.entities.hand import Hand, BirdHand
from src.entities.bird import Bird
from src.entities.deck import Deck
from src.entities.tray import Tray
from src.entities.gameboard import GameBoard
from unittest.mock import patch
from io import StringIO

class TestHand(unittest.TestCase):

    def setUp(self):
        self.hand = Hand()
        self.test_card = Bird("Osprey", 5, 2)

    def test_add_card(self):
        card_name = self.test_card.get_name()
        self.hand.add_card(self.test_card, card_name)
        self.assertIn(card_name, self.hand.cards)

    def test_get_card(self):
        card_name = self.test_card.get_name()
        self.hand.add_card(self.test_card, card_name)
        self.assertEqual(self.hand.get_card(card_name), self.test_card)

    def test_get_cards_in_hand(self):
        self.hand.add_card(self.test_card, self.test_card.get_name())
        self.assertEqual(self.hand.get_cards_in_hand(), [self.test_card])

    def test_get_card_names_in_hand(self):
        card_name = self.test_card.get_name()
        self.hand.add_card(self.test_card, card_name)
        self.assertEqual(self.hand.get_card_names_in_hand(), [card_name])

    def test_remove_card_type(self):
        card_name = self.test_card.get_name()
        self.hand.add_card(self.test_card, card_name)
        removed_card = self.hand.remove_card(card_name)
        self.assertNotIn(card_name, self.hand.cards)
        self.assertIsInstance(removed_card, Bird)

    def test_remove_card_not_in_hand(self):
        card_name = "Hermit Thrush"
        with self.assertRaises(ValueError):
            self.hand.remove_card(card_name)

    def test_draw_card_from_deck(self):
        deck = Deck()
        card_name = self.test_card.get_name()
        deck.add_card(self.test_card)
        self.hand.draw_card_from_deck(deck)
        self.assertIn(card_name, self.hand.get_card_names_in_hand())

    def test_draw_card_from_empty_deck(self):
        empty_deck = Deck()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.hand.draw_card_from_deck(empty_deck)
            self.assertEqual(fake_out.getvalue().strip(), "Error: Deck is empty")

    @patch.object(Hand, 'remove_card', return_value='Osprey')
    def test_discard_card(self, remove_card_mock):
        self.hand.add_card(self.test_card, self.test_card.get_name())
        discarded_card = self.hand.discard_card(self.test_card.get_name())

        remove_card_mock.assert_called_once()
        self.assertEqual(discarded_card, 'Osprey')

    def test_render(self):
        # check that render calls render_bird_container, and prints the returned value
        with patch('src.entities.hand.render_bird_container', return_value="Mocked render output") as mock_render, \
            patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.hand.render()
            self.assertEqual(mock_stdout.getvalue().strip(), "Mocked render output")
            mock_render.assert_called_once_with(bird_container=self.hand.get_card_names_in_hand())

class TestBirdHand(unittest.TestCase):

    def setUp(self):
        self.hand = BirdHand()
        self.birds = [Bird("Osprey", 5, 2), Bird("Peregrine Falcon", 3, 1), Bird("Anhinga", 4, 2)]

    def test_draw_bird_from_tray(self):
        tray = Tray()
        for bird in self.birds:
            tray.add_bird(bird)
        card_to_draw = self.birds[0].get_name()
        self.hand.draw_bird_from_tray(tray, card_to_draw)
        self.assertIn(card_to_draw, self.hand.get_card_names_in_hand())

    def test_play_bird(self):
        game_board = GameBoard()
        bird_name = "Osprey"
        self.hand.add_card(Bird(bird_name, 5, 2), bird_name)
        self.hand.play_bird(bird_name=bird_name, game_board=game_board)
        self.assertNotIn(bird_name, self.hand.cards)
        self.assertIn(bird_name, [bird.get_name() for bird in game_board.get_birds()])

    def test_tuck_card(self):
        card_name = "Osprey"
        self.hand.add_card(Bird(card_name, 5, 2), card_name)
        self.hand.tuck_card(card_name)
        self.assertNotIn(card_name, self.hand.cards)

    def test_to_representation(self):
        for bird in self.birds:
            self.hand.add_card(bird, bird.get_name())
        expected_representation = frozenset([bird.to_representation() for bird in self.birds])
        self.assertEqual(self.hand.to_representation(), expected_representation)

    def test_to_representation_empty_hand(self):
        self.assertEqual(self.hand.to_representation(), frozenset())

if __name__ == '__main__':
    unittest.main()