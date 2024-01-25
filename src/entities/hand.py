from src.utilities.utils import render_bird_container
from typing import Dict, List, FrozenSet, Tuple, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.bird import Bird #TODO: change to Card when Card is implemented as a superclass of Bird
    from src.entities.deck import Deck
    from src.entities.tray import Tray
    from src.entities.gameboard import GameBoard

class Hand:
    """A generic hand of cards, that can be used for both the player's bird cards and the player's bonus cards."""

    def __init__(self):
        self.cards: Dict[str, 'Bird'] = {}

    def add_card(self, card: 'Bird', card_name: str) -> None:
        """Add a card to the hand"""
        self.cards[card_name] = card

    def get_card(self, card_name: str) -> 'Bird':
        """Get a card from the hand"""
        return self.cards[card_name]

    def get_cards_in_hand(self) -> List['Bird']:
        """Public method that returns cards in hand"""
        return list(self.cards.values())
    
    def get_card_names_in_hand(self) -> List[str]:
        """Public method that returns card names in hand"""
        return list(self.cards.keys())

    def remove_card(self, card_name: str) -> 'Bird':
        """Remove a card from the hand and return it"""
        if card_name not in self.cards:
            raise ValueError(f"Card {card_name} not in hand")
        return self.cards.pop(card_name)

    def draw_card_from_deck(self, deck: 'Deck') -> None:
        """Draw a card from the deck and add it to the hand"""
        try:
            card = deck.draw_card()
            card_name = card.get_name()
            self.add_card(card, card_name)  # Pass the card_name parameter when calling add_card
        except ValueError as e:
            # Handle the case where the deck is empty
            print(f"Error: {str(e)}")

    def discard_card(self, card_name: str) -> 'Bird':
        """Discard a card from the hand"""
        return self.remove_card(card_name)
    
    def render(self) -> None:
        """Render the hand"""
        print(render_bird_container(bird_container=self.get_cards_in_hand()))

class BirdHand(Hand):
    """A hand specifically for bird cards"""

    def draw_bird_from_tray(self, tray: 'Tray', bird_name: str) -> None:
        """Draw a bird from the tray and add it to the hand"""
        bird = tray.draw_bird(bird_name)
        self.add_card(bird, card_name=bird_name)

    def play_bird(self, bird_name: str, game_board: 'GameBoard') -> None:
        """Play a bird from the hand"""
        game_board.add_bird(self.remove_card(bird_name))

    def tuck_card(self, card_name: str) -> None:
        """Tuck a card from the hand"""
        self.remove_card(card_name)

    def to_representation(self) -> FrozenSet[Tuple[int, int]]:
        """Return a representation of the hand for composing a representation of the game state."""
        return frozenset([card.to_representation() for card in self.get_cards_in_hand()])