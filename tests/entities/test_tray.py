import unittest
from src.entities.tray import Tray
from src.entities.bird import Bird
from src.entities.deck import Deck
from unittest.mock import patch
from io import StringIO

class TestTray(unittest.TestCase):
    def setUp(self):
        self.tray = Tray()
        self.birds =  birds = [
            Bird("Blue Jay", 5, 2),
            Bird("Cardinal", 3, 1),
            Bird("Barn Swallow", 3, 1)
        ]
        self.bird_deck = Deck()

    def test_get_count(self):
        # Test when the tray is empty
        self.assertEqual(self.tray.get_count(), 0)

        # Test when the tray has birds
        for bird in self.birds:
            self.tray.add_bird(bird)
        self.assertEqual(self.tray.get_count(), 3)

    def test_get_birds_in_tray(self):
        # Test when the tray is empty
        self.assertEqual(self.tray.get_birds_in_tray(), [])

        # Test when the tray has birds
        for bird in self.birds:
            self.tray.add_bird(bird)
        self.assertEqual(self.tray.get_birds_in_tray(), self.birds)

    def test_see_birds_in_tray(self):
        # Test when the tray is empty
        self.assertEqual(self.tray.see_birds_in_tray(), [])

        # Test when the tray has birds
        for bird in self.birds:
            self.tray.add_bird(bird)
        self.assertEqual(self.tray.see_birds_in_tray(), [bird.get_name() for bird in self.birds]) # keys are returned in the order they were inserted

    def test_draw_bird(self):
        bird = self.birds[0]
        self.tray.add_bird(bird)
        drawn_bird = self.tray.draw_bird(bird.get_name())
        self.assertEqual(drawn_bird, bird)
        self.assertEqual(self.tray.see_birds_in_tray(), [])

    def test_add_bird(self):
        bird = self.birds[0]
        self.tray.add_bird(bird)
        self.assertEqual(self.tray.see_birds_in_tray(), [bird.get_name()])

    def test_is_not_full(self):
        # Test when the tray is empty
        self.assertTrue(self.tray.is_not_full())

        # Test whe the tray is partially full
        self.tray.add_bird(self.birds[0])
        self.assertTrue(self.tray.is_not_full())

        # Test when the tray is full
        for bird in self.birds[1:]:
            self.tray.add_bird(bird)
        self.assertFalse(self.tray.is_not_full())

    def test_refill_when_empty(self):
        # Test when the tray is empty
        for bird in self.birds:
            self.bird_deck.add_card(bird)
        self.tray.refill(self.bird_deck)
        self.assertEqual(self.tray.see_birds_in_tray(), [bird.get_name() for bird in self.birds])

    def test_refill_when_partially_full(self):
        # Test when the tray is partially full
        for bird in self.birds:
            self.bird_deck.add_card(bird)
        self.tray.add_bird(self.birds[0])
        self.tray.refill(self.bird_deck)
        self.assertEqual(self.tray.see_birds_in_tray(), [bird.get_name() for bird in self.birds])

    def test_refill_when_deck_is_empty(self):
        # Test when the tray is partially full and the deck is empty
        self.tray.add_bird(self.birds[0])
        self.tray.refill(self.bird_deck)
        self.assertEqual(self.tray.see_birds_in_tray(), [self.birds[0].get_name()])

    def test_flush(self):
        # Test when the deck is empty
        discard_pile = Deck()
        empty_deck = Deck()
        self.tray.flush(discard_pile, empty_deck)
        self.assertEqual(self.tray.see_birds_in_tray(), [])

        # Test when the tray has birds
        for bird in self.birds:
            self.tray.add_bird(bird)
        full_deck = Deck()
        new_birds = [
            Bird("Osprey", 5, 2),
            Bird("Peregrine Falcon", 3, 1),
            Bird("Anhinga", 4, 2)
        ]
        for bird in new_birds:
            full_deck.add_card(bird)
        self.tray.flush(discard_pile, full_deck)
        self.assertEqual(self.tray.see_birds_in_tray(), [bird.get_name() for bird in new_birds[:3]])
        self.assertEqual(discard_pile.get_count(), 3)
    
    def test_render(self):
        # check that render calls render_bird_container, and prints the returned value
        with patch('src.entities.tray.render_bird_container', return_value="Mocked render output") as mock_render, \
            patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.tray.render()
            self.assertEqual(mock_stdout.getvalue().strip(), "Mocked render output")
            mock_render.assert_called_once_with(bird_container=self.tray.see_birds_in_tray(), capacity=self.tray.capacity)

    def test_to_representation_full_tray(self):
        # Test when the tray is full
        for bird in self.birds:
            self.tray.add_bird(bird)
        self.assertEqual(self.tray.to_representation(), frozenset([bird.to_representation() for bird in self.birds]))

    def test_to_representation_partially_full_tray(self):
        # Test when the tray is partially full
        for bird in self.birds[:2]:
            self.tray.add_bird(bird)
        expected_representation = frozenset([bird.to_representation() for bird in self.birds[:2]] + [Bird("Placeholder", 0, 0).to_representation()])
        self.assertEqual(self.tray.to_representation(), expected_representation)
            
if __name__ == '__main__':
    unittest.main()
