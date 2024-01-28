import random
from typing import List, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.bird import Bird

class Deck:
    def __init__(self, cards: List['Bird']=None):
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
    
    def prepare_deck(self, cards: List['Bird']) -> None:
        """
        Prepares a new deck of cards by adding each card to the deck and shuffling.

        Args:
            cards (List[Bird]): The list of cards to be added to the deck.
        """
        self.cards.extend(cards)
        self.shuffle()

    def add_card(self, card: 'Bird') -> None:
        """
        Adds a card to the deck.

        Args:
            card (Card): The card to be added to the deck.
        """
        self.cards.append(card)

    def remove_and_return_bird(self, condition: Callable[['Bird'], bool]) -> 'Bird':
        """
        Removes and returns the first bird in the deck that meets the given condition.

        Args:
            condition (function): A function that takes a Bird as an argument and returns a boolean.

        Returns:
            Bird: The first bird in the deck that meets the condition.

        Raises:
            ValueError: If no bird in the deck meets the condition.
        """
        for i, bird in enumerate(self.cards):
            if condition(bird):
                return self.cards.pop(i)
        raise ValueError('No bird in the deck meets the condition')

    def draw_card(self) -> 'Bird':
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
