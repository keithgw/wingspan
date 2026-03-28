from src.utilities.utils import render_bird_container


class Tray:
    def __init__(self, capacity=3):
        self.capacity = capacity
        self.birds = {}

    def get_count(self):
        """Public method that returns the number of birds in the tray."""
        return len(self.birds)

    def get_birds_in_tray(self):
        """Public method that returns a list of birds in the tray."""
        return [bird for bird in self.birds.values()]

    def see_birds_in_tray(self):
        """Public method that returns a list of birds in the tray."""
        return [bird for bird in self.birds.keys()]

    def draw_bird(self, common_name):
        """
        Draw a bird from the tray.

        Args:
            common_name (str): The common name of the bird to draw.
        """

        if common_name not in self.birds:
            raise ValueError(f"{common_name} does not exist in the tray.")
        return self.birds.pop(common_name)

    def add_bird(self, bird):
        """
        Add a bird to the tray.

        Args:
            bird (Bird): The bird to add.
        """
        self.birds[bird.get_name()] = bird

    def is_not_full(self):
        """Public method that returns True if the tray is not full, False otherwise."""
        return self.get_count() < self.capacity

    def refill(self, bird_deck):
        """
        Refill the tray with birds from the deck.

        Args:
            bird_deck (Deck): The bird deck.
        """

        while self.is_not_full() and bird_deck.get_count() > 0:
            bird = bird_deck.draw_card()
            self.add_bird(bird)

    def flush(self, discard_pile, bird_deck):
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

    def render(self):
        """Render the tray."""
        print(render_bird_container(bird_container=self.get_birds_in_tray(), capacity=self.capacity))

    def to_representation(self):
        """Return a sorted tuple of bird (points, food_cost) tuples with (0,0) for empty slots."""
        missing_birds = self.capacity - self.get_count()
        reps = [bird.to_representation() for bird in self.get_birds_in_tray()] + [(0, 0)] * missing_birds
        return tuple(sorted(reps))

    @classmethod
    def from_representation(cls, representation, deck):
        """Reconstruct a Tray from a representation by drawing matching birds from the deck."""
        capacity = len(representation)
        tray = cls(capacity=capacity)
        for bird_rep in representation:
            if bird_rep != (0, 0):
                bird = deck.remove_and_return_bird(lambda b, rep=bird_rep: b.to_representation() == rep)
                tray.add_bird(bird)
        return tray
