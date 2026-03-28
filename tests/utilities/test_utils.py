import unittest

from src.entities.bird import Bird
from src.utilities.utils import render_bird_container


class TestUtils(unittest.TestCase):
    def setUp(self):
        self.bird_container = [
            Bird("Osprey", 5, 1),
            Bird("Bald Eagle", 9, 3),
            Bird("Peregrine Falcon", 5, 2),
        ]

    def test_render_bird_container_with_capacity(self):
        output = render_bird_container(self.bird_container, capacity=5)
        # Should contain all birds plus empty slots
        self.assertIn("Osprey", output)
        self.assertIn("Bald Eagle", output)
        self.assertIn("Peregrine Falcon", output)
        # 3 birds + 2 empty slots = 5 lines + header
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 6)  # header + 5 slots

    def test_render_bird_container_without_capacity(self):
        output = render_bird_container(self.bird_container)
        self.assertIn("Osprey", output)
        self.assertIn("Bald Eagle", output)
        self.assertIn("Peregrine Falcon", output)
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 4)  # header + 3 birds, no empty slots

    def test_render_bird_container_with_empty_slots(self):
        output = render_bird_container([], capacity=5)
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 6)  # header + 5 empty slots
        # No bird names, only empty slot markers
        self.assertNotIn("Osprey", output)

    def test_render_shows_points_and_cost(self):
        output = render_bird_container(self.bird_container)
        # Osprey: 5 VP, 1 food cost
        self.assertIn("5", output)
        self.assertIn("1", output)


if __name__ == "__main__":
    unittest.main()
