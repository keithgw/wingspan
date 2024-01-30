from src.constants import CHOOSE_A_BIRD_TO_PLAY, CHOOSE_A_BIRD_TO_DRAW
from src.entities.gameboard import GameBoard
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from src.entities.game_state import GameState
    from src.entities.tray import Tray
    from src.entities.deck import Deck
    from src.entities.birdfeeder import BirdFeeder

class Player:
    def __init__(self, name, bird_hand, food_supply, num_turns_remaining, game_board=None):
        self.name = name
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.turns_remaining = num_turns_remaining
        if game_board is None:
            self.game_board = GameBoard()
        else:
            self.game_board = game_board
        self.score = 0
        self.actions = ["play_a_bird", "gain_food", "draw_a_bird"] # lay_eggs not implemented yet #TODO: get from constants.py

    def get_name(self):
        '''
        Returns the name of the player.
        '''
        return self.name
    
    def set_name(self, name):
        '''
        Sets the name of the player.
        '''
        self.name = name
        
    def get_bird_hand(self):
        '''
        Returns the bird hand associated with the player.
        '''
        return self.bird_hand
    
    def get_food_supply(self):
        '''
        Returns the food supply associated with the player.
        '''
        return self.food_supply
    
    def get_game_board(self):
        '''
        Returns the game board associated with the player.
        '''
        return self.game_board
    
    def _enumerate_playable_birds(self) -> List[str]:
        '''
        Enumerates the birds that the player can play. 
        A bird is playable if it is in the player's hand and the player has enough food to play it.
        '''
        return [bird.get_name() for bird in self.bird_hand.get_cards_in_hand() if self.food_supply.can_play_bird(bird)]
    
    def _enumerate_legal_actions(self, tray: 'Tray', bird_deck: 'Deck') -> List[str]:
        '''
        Enumerates the legal actions based on the current game state.
        
        Args:
            tray (Tray): The bird tray.
            bird_deck (Deck): The bird deck.
        '''

        legal_actions = []

        # Check if player can play a bird
        ## player must have space on the board
        if not self.game_board.check_if_full():
            ## player must have a bird in hand with enough food to play it
            if len(self._enumerate_playable_birds()) > 0:
                legal_actions.append(self.actions[0])
        
        # Player can always gain food
        legal_actions.append(self.actions[1])

        # Check if player can draw a bird
        if bird_deck.get_count() > 0 or tray.get_count() > 0:
            legal_actions.append(self.actions[2])

        return legal_actions
    
    def _choose_action(self, legal_actions: List[str], game_state: 'GameState') -> str:
        '''
        Prompts the player to choose an action and returns the chosen action.

        Args:
            legal_actions (List[str]): The legal actions for the player.
            game_state (GameState): The current game state.

        Returns:
            chosen_action (str): The chosen action by the player.
        '''
        raise NotImplementedError

    def request_action(self, game_state: 'GameState') -> str:
        '''
        Chooses an action to take based on the current game state and returns it.

        Args:
            game_state (GameState): The current game state.
        '''
        # determine the legal actions
        legal_actions = self._enumerate_legal_actions(tray=game_state.get_tray(), bird_deck=game_state.get_bird_deck())
        action = self._choose_action(legal_actions=legal_actions, game_state=game_state)
        return action
    
    def take_action(self, action: str, game_state: 'GameState') -> None:
        '''
        Takes an action based on the current game state.

        Args:
            action (str): The action to take.
            game_state (GameState): The current game state.
        '''
        if action not in self.actions:
            raise Exception(f"Action {action} is not valid.")
        elif action == self.actions[0]:
            self.play_a_bird(game_state)
        elif action == self.actions[1]:
            self.gain_food(game_state.get_bird_feeder())
        else:
            self.draw_a_bird(game_state)

    def _choose_a_bird_to_play(self, playable_birds: List[str], game_state: 'GameState') -> str:
        '''
        Prompts the player to choose a bird from their hand.

        Args:
            playable_birds (List[str]): The birds that the player has in hand and has the food to play.
            game_state (GameState): The current game state.

        Returns:
            chosen_bird (str): The name of the chosen bird.
        '''
        raise NotImplementedError
    
    def play_a_bird(self, game_state: 'GameState') -> None:
        '''
        Player is prompted to choose a bird from their hand, and the bird is played to their game board.
        '''
        # determine the playable birds from the player's hand
        playable_birds = self._enumerate_playable_birds()

        # prompt the player to choose a bird to play
        bird_name = self._choose_a_bird_to_play(playable_birds=playable_birds, game_state=game_state)

        # remove the food cost from the player's food supply
        food_cost = self.bird_hand.get_card(bird_name).get_food_cost()
        self.food_supply.decrement(food_cost)

        # play the bird to the player's game board
        self.bird_hand.play_bird(bird_name=bird_name, game_board=self.game_board)
    
    def gain_food(self, bird_feeder: 'BirdFeeder') -> None:
        '''
        Player gains food from the bird feeder.

        Args:
            bird_feeder (BirdFeeder): The bird feeder.
        '''
        # take one food at a time
        bird_feeder.take_food()
        self.food_supply.increment(1)

    def _choose_a_bird_to_draw(self, valid_choices: List[str], game_state: 'GameState') -> str:
        '''
        Prompt the player to choose a bird to draw from either the bird deck or the tray.

        Args:
            valid_choices (List[str]): A list of bird names in the tray and/or 'deck'.
            game_state (GameState): The current game state.

        Returns:
            chosen_bird (str): The name of the chosen bird, 'deck' if drawing from the deck.
        '''
        raise NotImplementedError

    def draw_a_bird(self, game_state: 'GameState') -> None:

        # Get the tray and bird deck
        tray = game_state.get_tray()
        bird_deck = game_state.get_bird_deck()

        # Get the bird names from the tray and determine if there are cards in the bird deck
        valid_choices = tray.see_birds_in_tray()
        if bird_deck.get_count() > 0:
            valid_choices.append("deck")

        # Prompt the player to choose a bird
        chosen_bird = self._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=game_state)

        # Remove the bird from the tray or deck
        if chosen_bird == "deck":
            try:
                self.bird_hand.draw_card_from_deck(bird_deck)
                print(f"You drew {self.bird_hand.get_card_names_in_hand()[-1]} from the deck.")
            except Exception as e:
                # this should only happen if the deck is empty, but the user knows to type 'deck' in that case
                print(f"Error: {e}")
                chosen_bird = self._choose_a_bird_to_draw(valid_choices=valid_choices, game_state=game_state)
        else:
            self.bird_hand.draw_bird_from_tray(tray=tray, bird_name=chosen_bird)

    def get_score(self):
        '''
        Returns the player's score.
        '''
        return self.score
            
    def end_turn(self):
        '''
        Ends the player's turn.
        '''
        # decrement the player's turn count
        self.turns_remaining -= 1

        # update the player's score
        self.score = self.game_board.get_score()

    def get_turns_remaining(self):
        '''
        Returns the number of turns remaining for the player.
        '''
        return self.turns_remaining

class HumanPlayer(Player):
    def _choose_action(self, legal_actions: List[str], game_state: 'GameState') -> str:
        '''
        Prompts the player to choose an action and returns the chosen action.

        Args:
            legal_actions (List[str]): The legal actions for the player.
            game_state (GameState): The current game state. Not used in this subclass.

        Returns:
            chosen_action (str): The chosen action by the player.
        '''
        actions_map = {
            '1': self.actions[0],
            '2': self.actions[1],
            '3': self.actions[2]
        }
        
        # Prompt the player to choose an action
        prompt = "Type 1 to play a bird, 2 to gain food, or 3 to draw a bird."
        chosen_action = input(prompt).strip()

        # Check if the chosen action is legal
        while actions_map[chosen_action] not in legal_actions:
            print(f"You are unable to {actions_map[chosen_action]}. {prompt}")
            chosen_action = input(prompt).strip()

        return actions_map[chosen_action]

    def _choose_a_bird_to_play(self, playable_birds: List[str], game_state: 'GameState') -> str:
        '''
        Prompts the player to choose a bird from their hand.

        Args:
            playable_birds (List[str]): The birds that the player has in hand and has the food to play.
            game_state (GameState): The current game state. Not used in this subclass.

        Returns:
            chosen_bird (str): The name of the chosen bird.
        '''
        prompt = "Choose a bird to play: " + "\n" + "\n".join(playable_birds) + "\n"
        chosen_bird = input(prompt)
        while chosen_bird not in self.bird_hand.get_card_names_in_hand():
            print(f"{chosen_bird} is not a valid bird. {prompt}")
            chosen_bird = input(prompt)

        return chosen_bird

    def _choose_a_bird_to_draw(self, valid_choices: List[str], game_state: 'GameState') -> str:
        '''
        Prompt the player to choose a bird to draw from either the bird deck or the tray.

        Args:
            valid_choices (List[str]): A list of bird names in the tray and/or 'deck'.
            game_state (GameState): The current game state. Not used in this subclass.

        Returns:
            chosen_bird (str): The name of the chosen bird, 'deck' if drawing from the deck.
        '''
        # Construct prompts
        birds_in_tray = [bird for bird in valid_choices if bird != "deck"]
        prompt_from_tray = "Choose a bird from the tray: " + "\n" +  "\n".join(birds_in_tray)
        prompt_from_deck = "type 'deck' to draw from the bird deck."
        tray_is_empty = len(birds_in_tray) == 0
        if tray_is_empty:
            prompt = "The tray is empty, " + prompt_from_deck
        elif "deck" not in valid_choices:
            prompt = prompt_from_tray
        else:
            prompt = prompt_from_tray + "\nor " + prompt_from_deck

        # Prompt the player to choose a bird
        chosen_bird = input(prompt).strip()
        while chosen_bird not in valid_choices:
            print(f"{chosen_bird} is not a valid choice.")
            chosen_bird = input(prompt).strip()

        return chosen_bird

class BotPlayer(Player):
    def __init__(self, policy, *args, **kwargs):
        super().__init__(*args, **kwargs)
        '''
        Args:
            policy (Policy): The policy to use for the bot. If None, a random policy will be used.
        '''
        self.policy = policy  # Load learned policy here

        #TODO: add known missing cards

    def _choose_action(self, legal_actions: List[str], game_state: 'GameState') -> str:
        # Use the policy to choose an action according to the probabilities
        action = self.policy(state=game_state, actions=legal_actions)

        # Update the phase of the game state, if more choices are required to complete the player's turn
        if action == self.actions[0]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_PLAY)
        elif action == self.actions[2]:
            game_state.set_phase(CHOOSE_A_BIRD_TO_DRAW)

        return action

    def _choose_a_bird_to_play(self, playable_birds: List[str], game_state: 'GameState') -> str:
        # Use the policy to choose a bird according to the probabilities
        return self.policy(state=game_state, actions=playable_birds)
        
    def _choose_a_bird_to_draw(self, valid_choices: List[str], game_state: 'GameState') -> str:
        # Use the policy to choose a bird from the tray or deck according to the probabilities
        return self.policy(state=game_state, actions=valid_choices)