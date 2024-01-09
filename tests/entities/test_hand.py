import unittest
from src.entities.hand import Hand, BirdHand
from src.entities.bird import Bird
from src.entities.deck import Deck
from src.entities.tray import Tray

class TestHand(unittest.TestCase):

    def setUp(self):
        self.hand = Hand()
        self.test_card = Bird("Osprey", 5, 2)

        def test_add_card(self):
            card_name = self.test_card.get_name()
            self.hand.add_card(self.test_card, card_name)
            self.assertIn(card_name, self.hand.cards)

        def test_get_cards_in_hand(self):
            card_name = self.test_card.get_name()
            self.hand.add_card(self.test_card, card_name)
            self.assertEqual(self.hand.get_cards_in_hand(), [card_name])

        def test_remove_card(self):
            card_name = self.test_card.get_name()
            self.hand.add_card(self.test_card, card_name)
            self.hand.remove_card(card_name)
            self.assertNotIn(card_name, self.hand.cards)

        def test_remove_card_not_in_hand(self):
            card_name = "Hermit Thrush"
            with self.assertRaises(ValueError):
                self.hand.remove_card(card_name)

        def test_draw_card_from_deck(self):
            deck = Deck()
            deck.add_card("Osprey")
            deck.add_card("Peregrine Falcon")
            self.hand.draw_card_from_deck(deck)
            self.assertIn("Osprey", self.hand.cards)

        def test_draw_card_from_empty_deck(self):
            deck = Deck()
            with self.assertRaises(ValueError):
                self.hand.draw_card_from_deck(deck)

        def test_discard_card(self):
            card_name = self.test_card.get_name()
            self.hand.add_card(self.test_card, card_name)
            self.hand.discard_card(card_name)
            self.assertNotIn(card_name, self.hand.cards)

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
        self.assertIn(card_to_draw, self.hand.get_cards_in_hand())

    def test_play_bird(self):
        card_name = "Osprey"
        self.hand.add_card(Bird(card_name, 5, 2), card_name)
        self.hand.play_bird(card_name)
        self.assertNotIn(card_name, self.hand.cards)

    def test_tuck_card(self):
        card_name = "Osprey"
        self.hand.add_card(Bird(card_name, 5, 2), card_name)
        self.hand.tuck_card(card_name)
        self.assertNotIn(card_name, self.hand.cards)

if __name__ == '__main__':
    unittest.main()