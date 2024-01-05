import unittest
from src.entities.bird import Bird

class TestBird(unittest.TestCase):
    def test_init(self):
        bird = Bird('Osprey', 5, 2)
        self.assertEqual(bird.common_name, 'Osprey')
        self.assertEqual(bird.points, 5)
        self.assertEqual(bird.food_cost, 2)