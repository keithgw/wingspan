from src.entities.bird import Bird
from src.utilities.utils import render_bird_container
from typing import List, FrozenSet, Tuple ,TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.deck import Deck

class Tray:
    def __init__(self, capacity: int=3) -> None:
        self.capacity = capacity
        self.birds = {}

    def get_count(self) -> int:
        """Public method that returns the number of birds in the tray."""
        return len(self.birds)
    
    def get_birds_in_tray(self) -> List[Bird]:
        """Public method that returns a list of birds in the tray."""
        return [bird for bird in self.birds.values()]

    def see_birds_in_tray(self) -> List[str]:
        """Public method that returns a list of birds in the tray."""
        return [bird for bird in self.birds.keys()]

    def draw_bird(self, common_name: str) -> Bird:
        """
        Draw a bird from the tray.
        
        Args:
            common_name (str): The common name of the bird to draw.
        """

        if common_name not in self.birds:
            raise ValueError(f"{common_name} does not exist in the tray.")
        return self.birds.pop(common_name)

    def add_bird(self, bird: Bird) -> None:
        """
        Add a bird to the tray.
        
        Args:
            bird (Bird): The bird to add.
        """
        self.birds[bird.get_name()] = bird

    def is_not_full(self):
        """Public method that returns True if the tray is not full, False otherwise."""
        return self.get_count() < self.capacity
    
    def refill(self, bird_deck: 'Deck') -> None:
        """
        Refill the tray with birds from the deck.
        
        Args:
            bird_deck (Deck): The bird deck.
        """

        while self.is_not_full() and bird_deck.get_count() > 0:
            bird = bird_deck.draw_card()
            self.add_bird(bird)

        #TODO: return birds that were added to the tray for use in tracking known_missing_birds

    def flush(self, discard_pile: 'Deck', bird_deck: 'Deck') -> None:
        """
        Flush the tray and add all birds to the discard pile.
        Refill the tray with birds from the deck.
        
        Args:
            discard_pile (Deck): The discard pile.
            bird_deck (Deck): The bird deck.
        """

        while len(self.birds) > 0:
            discard_pile.add_card(self.birds.popitem()[1])
        
        self.refill(bird_deck)

        #TODO: return birds that were added to the tray, the return from self.refill

    def render(self):
        """Render the tray."""
        print(render_bird_container(bird_container=self.get_birds_in_tray(), capacity=self.capacity))

    def to_representation(self) -> FrozenSet[Tuple[int, int]]:
        """Get the representation of the tray for use in composing state representations."""
        # Check if there are any empty spaces in the tray
        missing_birds = self.capacity - self.get_count()

        # Create a list of placeholder birds and extend the original list
        birds_to_represent = self.get_birds_in_tray()
        birds_to_represent.extend([Bird("Placeholder", 0, 0) for _ in range(missing_birds)])

        # Create the representation and return it
        return frozenset(bird.to_representation() for bird in birds_to_represent)
    
    @classmethod
    def from_representation(cls, representation: FrozenSet[Tuple[int, int]], deck: 'Deck') -> 'Tray':
        """Create a tray from a representation."""
        # infer the tray capacity from the representation
        capacity = len(representation)

        # Create a tray with the inferred capacity
        tray = cls(capacity=capacity)

        # For each bird in the representation, draw a valid bird from the deck and add it to the tray
        for bird_representation in representation:
            # handle empty slots, which are represented by (0, 0)
            if bird_representation != (0, 0):
                bird = deck.remove_and_return_bird(lambda bird: bird.to_representation() == bird_representation)
                tray.add_bird(bird)

        return tray