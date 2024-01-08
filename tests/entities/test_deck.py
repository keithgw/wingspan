import unittest
from src.entities.deck import Deck

class TestDeck(unittest.TestCase):
    def test_add_card(self):
        deck = Deck()
        deck.add_card('Osprey')
        self.assertEqual(deck.cards, ['Osprey'])

    def test_draw_card(self):
        deck = Deck(['Osprey', 'Barn Swallow'])
        card = deck.draw_card()
        self.assertEqual(card, 'Osprey')
        self.assertEqual(deck.cards, ['Barn Swallow'])

    def test_draw_card_with_empty_deck(self):
        deck = Deck()
        with self.assertRaises(ValueError):
            deck.draw_card()

    def test_shuffle_deck(self):
        deck = Deck(['Osprey', 'Barn Swallow'])
        deck.shuffle_deck()
        self.assertEqual(len(deck.cards), 2)

if __name__ == '__main__':
    unittest.main()
