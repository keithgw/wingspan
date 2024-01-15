from src.utilities.utils import render_bird_container

class Hand:
    '''A generic hand of cards, that can be used for both the player's bird cards and the player's bonus cards.'''

    def __init__(self):
        self.cards = {}

    def add_card(self, card, card_name):
        '''Add a card to the hand'''
        self.cards[card_name] = card

    def get_card(self, card_name):
        '''Get a card from the hand'''
        return self.cards[card_name]

    def get_cards_in_hand(self):
        '''Public method that returns cards in hand'''
        return list(self.cards.values())
    
    def get_card_names_in_hand(self):
        '''Public method that returns card names in hand'''
        return list(self.cards.keys())

    def remove_card(self, card_name):
        '''Remove a card from the hand and return it'''
        if card_name not in self.cards:
            raise ValueError(f"Card {card_name} not in hand")
        return self.cards.pop(card_name)

    def draw_card_from_deck(self, deck):
        '''Draw a card from the deck and add it to the hand'''
        try:
            card = deck.draw_card()
            card_name = card.get_name()
            self.add_card(card, card_name)  # Pass the card_name parameter when calling add_card
        except ValueError as e:
            # Handle the case where the deck is empty
            print(f"Error: {str(e)}")

    def discard_card(self, card_name):
        '''Discard a card from the hand'''
        return self.remove_card(card_name)
    
    def render(self):
        '''Render the hand'''
        print(render_bird_container(bird_container=self.get_cards_in_hand()))

class BirdHand(Hand):
    '''A hand specifically for bird cards'''

    def draw_bird_from_tray(self, tray, bird_name):
        '''Draw a bird from the tray and add it to the hand'''
        bird = tray.draw_bird(bird_name)
        self.add_card(bird, card_name=bird_name)

    def play_bird(self, bird_name, game_board):
        '''Play a bird from the hand'''
        game_board.add_card(self.remove_card(bird_name))

    def tuck_card(self, card_name):
        '''Tuck a card from the hand'''
        self.remove_card(card_name)