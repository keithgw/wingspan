from src.entities.bird import Bird

class Tray:
    def __init__(self):
        self.birds = {}

    def get_count(self):
        '''Public method that returns the number of birds in the tray.'''
        return len(self.birds)

    def see_birds_in_tray(self):
        '''Public method that returns a list of birds in the tray.'''
        return [bird for bird in self.birds.keys()]

    def draw_bird(self, common_name):
        '''
        Draw a bird from the tray.
        
        :param common_name: The common name of the bird to draw.
        :type common_name: str
        '''

        if common_name not in self.birds:
            raise ValueError(f"{common_name} does not exist in the tray.")
        return self.birds.pop(common_name)
    
    def flush(self, discard_pile, bird_deck):
        '''
        Flush the tray and add all birds to the discard pile.
        Refill the tray with birds from the deck.
        
        :param dicsard_pile: The discard pile.
        :type deck: Deck
        :param bird_deck: The bird deck
        :type deck: Deck
        '''

        while len(self.birds) > 0:
            discard_pile.add_card(self.birds.popitem()[1])
        
        while len(self.birds) < 3 and bird_deck.get_count() > 0:
            bird = bird_deck.draw_card()
            self.add_bird(bird)

    def add_bird(self, bird):
        '''
        Add a bird to the tray.
        
        :param bird: The bird to add.
        :type bird: Bird
        '''
        self.birds[bird.get_name()] = bird
