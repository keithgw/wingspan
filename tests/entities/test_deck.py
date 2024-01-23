import unittest
from src.entities.deck import Deck
from src.entities.bird import Bird

class TestDeck(unittest.TestCase):
    def setUp(self):
        self.deck = Deck()
        self.birds = [Bird("Osprey", 5, 2), Bird("Barn Swallow", 3, 1)]

    def test_add_card(self):
        self.deck.add_card(self.birds[0])
        self.assertEqual(self.deck.cards, [self.birds[0]])

    def test_draw_card(self):
        print(self.deck.get_count())
        for bird in self.birds:
            self.deck.add_card(bird)
        card = self.deck.draw_card()
        self.assertEqual(card.get_name(), self.birds[0].get_name()) # the first card should have been drawn
        self.assertEqual(self.deck.get_count(), 1) # there should be one card left in the deck

    def test_draw_card_with_empty_deck(self):
        with self.assertRaises(ValueError):
            self.deck.draw_card()

    def test_shuffle(self):
        # Create a large, but simple deck to make failure due to shuffling returning the same exact deck unlikely.
        for letter in "abcdefghijkl":
            self.deck.add_card(letter)
        original_deck = self.deck.cards.copy()
        self.deck.shuffle()
        # Check that the deck has the same cards after shuffling
        self.assertEqual(set(self.deck.cards), set(original_deck))
        # Check that the order of cards has changed (most of the time)
        self.assertNotEqual(self.deck.cards, original_deck)

if __name__ == '__main__':
    unittest.main()
