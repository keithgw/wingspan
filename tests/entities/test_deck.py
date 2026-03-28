import unittest

from src.entities.bird import Bird
from src.entities.deck import Deck


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
        self.assertEqual(card.get_name(), self.birds[0].get_name())  # the first card should have been drawn
        self.assertEqual(self.deck.get_count(), 1)  # there should be one card left in the deck

    def test_draw_card_with_empty_deck(self):
        with self.assertRaises(ValueError):
            self.deck.draw_card()

    def test_prepare_deck(self):
        # Use enough cards to make shuffling returning the same order unlikely
        cards = [f"bird_{i}" for i in range(12)]
        original_order = list(cards)
        self.deck.prepare_deck(cards)
        # All cards are present
        self.assertEqual(self.deck.get_count(), 12)
        self.assertEqual(set(self.deck.cards), set(original_order))
        # Order has been shuffled
        self.assertNotEqual(self.deck.cards, original_order)

    def test_remove_and_return_bird(self):
        for bird in self.birds:
            self.deck.add_card(bird)
        bird = self.deck.remove_and_return_bird(lambda b: b.get_name() == "Osprey")
        self.assertEqual(bird.get_name(), "Osprey")
        self.assertEqual(self.deck.get_count(), 1)

    def test_remove_and_return_bird_no_match(self):
        self.deck.add_card(self.birds[0])
        with self.assertRaises(ValueError):
            self.deck.remove_and_return_bird(lambda b: b.get_name() == "Nonexistent")


if __name__ == "__main__":
    unittest.main()
