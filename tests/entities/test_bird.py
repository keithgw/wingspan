import unittest
from src.entities.bird import Bird

class TestBird(unittest.TestCase):
    def test_init(self):
        bird = Bird('Osprey', 5, 2)
        self.assertEqual(bird.common_name, 'Osprey')
        self.assertEqual(bird.points, 5)
        self.assertEqual(bird.food_cost, 2)

    def test_get_name(self):
        bird = Bird('Osprey', 5, 2)
        self.assertEqual(bird.get_name(), 'Osprey')

    def test_get_points(self):
        bird = Bird('Osprey', 5, 2)
        self.assertEqual(bird.get_points(), 5)

    def test_get_food_cost(self):
        bird = Bird('Osprey', 5, 2)
        self.assertEqual(bird.get_food_cost(), 2)

    def test_activate(self):
        bird = Bird('Osprey', 5, 2)
        # Add test for activation behavior here
        pass

if __name__ == '__main__':
    unittest.main()