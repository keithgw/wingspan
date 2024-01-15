import unittest
from src.utilities.utils import render_bird_container
from src.entities.bird import Bird

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.bird_container = [Bird('Osprey', 5, 1), Bird('Bald Eagle', 9, 3), Bird('Peregrine Falcon', 5, 2)]

    def test_render_bird_container_with_capacity(self):
        # 5 slots, for example a game board
        capacity = 5

        expected_output =  "Bird Name                     Point Value    Food Cost \n"
        expected_output += "Osprey                        5              1         \n"
        expected_output += "Bald Eagle                    9              3         \n"
        expected_output += "Peregrine Falcon              5              2         \n"
        expected_output += "empty                         --             --        \n"
        expected_output += "empty                         --             --        \n"

        output = render_bird_container(self.bird_container, capacity)
        self.assertEqual(output, expected_output)

    def test_render_bird_container_without_capacity(self):
        # 3 slots, for example a bid hand, which should not render empty slots

        expected_output =  "Bird Name                     Point Value    Food Cost \n"
        expected_output += "Osprey                        5              1         \n"
        expected_output += "Bald Eagle                    9              3         \n"
        expected_output += "Peregrine Falcon              5              2         \n"

        output = render_bird_container(self.bird_container)
        self.assertEqual(output, expected_output)

    def test_render_bird_container_with_empty_slots(self):
        # Create an empty bird container with a capacity of 5
        bird_container = []
        capacity = 5

        expected_output = "Bird Name                     Point Value    Food Cost \n"
        expected_output += "empty                         --             --        \n"
        expected_output += "empty                         --             --        \n"
        expected_output += "empty                         --             --        \n"
        expected_output += "empty                         --             --        \n"
        expected_output += "empty                         --             --        \n"

        output = render_bird_container(bird_container, capacity)
        self.assertEqual(output, expected_output)

if __name__ == '__main__':
    unittest.main()