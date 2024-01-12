import random

class Deck:
    def __init__(self, cards=None):
        if cards is None:
            self.cards = []
        else:
            self.cards = cards

    def get_count(self):
        return len(self.cards)

    def add_card(self, card):
        self.cards.append(card)

    def draw_card(self):
        if self.get_count() == 0:
            raise ValueError('Deck is empty')
        # cards will be drawn from the top of the deck
        return self.cards.pop(0) 
    
    def shuffle_deck(self):
        random.shuffle(self.cards)