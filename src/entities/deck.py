from src.entities.bird import Bird
from typing import List
import random

class Deck:
    def __init__(self, cards: List[Bird]=None):
        """
        Initializes a new instance of the Deck class.

        Args:
            cards (List[Bird], optional): The list of cards in the deck. Defaults to None.
        """
        if cards is None:
            self.cards = []
        else:
            self.cards = cards

    def get_count(self) -> int:
        """
        Returns the number of cards in the deck.

        Returns:
            int: The number of cards in the deck.
        """
        return len(self.cards)

    def add_card(self, card: Bird) -> None:
        """
        Adds a card to the deck.

        Args:
            card (Card): The card to be added to the deck.
        """
        self.cards.append(card)

    def draw_card(self) -> Bird:
        """
        Draws a card from the top of the deck.

        Returns:
            Card: The card drawn from the deck.

        Raises:
            ValueError: If the deck is empty.
        """
        if self.get_count() == 0:
            raise ValueError('Deck is empty')
        return self.cards.pop(0) 
    
    def shuffle(self) -> None:
        """
        Shuffles the cards in the deck.
        """
        random.shuffle(self.cards)
