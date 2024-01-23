from src.entities.bird import Bird
from src.utilities.utils import render_bird_container

class Tray:
    def __init__(self, capacity=3):
        self.capacity = capacity
        self.birds = {}

    def get_count(self):
        '''Public method that returns the number of birds in the tray.'''
        return len(self.birds)
    
    def get_birds_in_tray(self):
        '''Public method that returns a list of birds in the tray.'''
        return [bird for bird in self.birds.values()]

    def see_birds_in_tray(self):
        '''Public method that returns a list of birds in the tray.'''
        return [bird for bird in self.birds.keys()]

    def draw_bird(self, common_name):
        '''
        Draw a bird from the tray.
        
        Args:
            common_name (str): The common name of the bird to draw.
        '''

        if common_name not in self.birds:
            raise ValueError(f"{common_name} does not exist in the tray.")
        return self.birds.pop(common_name)

    def add_bird(self, bird):
        '''
        Add a bird to the tray.
        
        Args:
            bird (Bird): The bird to add.
        '''
        self.birds[bird.get_name()] = bird

    def is_not_full(self):
        '''Public method that returns True if the tray is not full, False otherwise.'''
        return self.get_count() < self.capacity
    
    def refill(self, bird_deck):
        '''
        Refill the tray with birds from the deck.
        
        Args:
            bird_deck (Deck): The bird deck.
        '''

        while self.is_not_full() and bird_deck.get_count() > 0:
            bird = bird_deck.draw_card()
            self.add_bird(bird)

        #TODO: return birds taht were added to the tray

    def flush(self, discard_pile, bird_deck):
        '''
        Flush the tray and add all birds to the discard pile.
        Refill the tray with birds from the deck.
        
        Args:
            discard_pile (Deck): The discard pile.
            bird_deck (Deck): The bird deck.
        '''

        while len(self.birds) > 0:
            discard_pile.add_card(self.birds.popitem()[1])
        
        self.refill(bird_deck)

        #TODO: return birds that were added to the tray

    def render(self):
        '''Render the tray.'''
        print(render_bird_container(bird_container=self.get_birds_in_tray(), capacity=self.capacity))