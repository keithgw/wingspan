from src.utilities.utils import render_bird_container

class GameBoard:
    def __init__(self, capacity=5):
        self.capacity = capacity
        self.birds = []

    def get_birds(self):
        '''Public getter for the birds on the game board.'''
        return self.birds
    
    def check_if_full(self):
        '''Returns True if the game board is full, False otherwise.'''
        return len(self.birds) == self.capacity

    def add_bird(self, bird):
        '''
        Adds a bird to the game board.
        
        Args:
            bird (Bird): The bird to add to the game board.
        '''
        if self.check_if_full():
            raise ValueError("Game board is full. Cannot add more birds.")
        self.birds.append(bird)

    def render(self):
        '''Renders the game board.'''
        print(render_bird_container(bird_container=self.get_birds(), capacity=self.capacity))

    def get_score(self):
        '''
        Returns the score of the game board.
        '''
        return sum([bird.get_points() for bird in self.birds])
