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

    def test_get_count(self):
        # Test when the tray is empty
        self.assertEqual(self.tray.get_count(), 0)

        # Test when the tray has birds
        for bird in self.birds:
            self.tray.add_bird(bird)
        self.assertEqual(self.tray.get_count(), 3)

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
if __name__ == '__main__':
    unittest.main()
