from src.utilities.utils import render_bird_container
from typing import List, FrozenSet, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.deck import Deck
from src.entities.bird import Bird

class GameBoard:
    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.birds: List['Bird'] = []

    def get_birds(self) -> List['Bird']:
        """Public getter for the birds on the game board."""
        return self.birds
    
    def check_if_full(self) -> bool:
        """Returns True if the game board is full, False otherwise."""
        return len(self.birds) == self.capacity

    def add_bird(self, bird: 'Bird') -> None:
        """
        Adds a bird to the game board.
        
        Args:
            bird (Bird): The bird to add to the game board.
        """
        if self.check_if_full():
            raise ValueError("Game board is full. Cannot add more birds.")
        self.birds.append(bird)

    def render(self) -> None:
        """Renders the game board."""
        print(render_bird_container(bird_container=self.get_birds(), capacity=self.capacity))

    def get_score(self) -> int:
        """
        Returns the score of the game board.
        """
        return sum([bird.get_points() for bird in self.birds])
    
    def to_representation(self) -> FrozenSet[Tuple[int, int]]:
        """
        Returns a representation of the game board for use in composing state representations.
        """
        # Check if there are available spaces on the game board
        open_spaces = self.capacity - len(self.birds)

        # Create a list of placeholder birds and extend the original list
        birds_to_represent = self.get_birds()
        birds_to_represent.extend([Bird("Placeholder", 0, 0) for _ in range(open_spaces)])

        # Create the representation and return it
        return frozenset([bird.to_representation() for bird in birds_to_represent])
    
    @classmethod
    def from_representation(cls, representation: FrozenSet[Tuple[int, int]], deck: 'Deck') -> 'GameBoard':
        """
        Returns a GameBoard from a representation of the game board.
        
        Args:
            representation (FrozenSet[Tuple[int, int]]): A representation of the game board.
        """
        # infer the tray capacity from the representation
        capacity = len(representation)

        # Create a tray with the inferred capacity
        gameboard = cls(capacity=capacity)

        # For each bird in the representation, draw a valid bird from the deck and add it to the tray
        for bird_representation in representation:
            # handle empty slots, which are represented by (0, 0)
            if bird_representation != (0, 0):
                bird = deck.remove_and_return_bird(lambda bird: bird.to_representation() == bird_representation)
                gameboard.add_bird(bird)

        return gameboard
