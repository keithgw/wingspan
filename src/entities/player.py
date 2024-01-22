from src.entities.gameboard import GameBoard
from src.rl.reinforcement_learning import State, RandomPolicy
import numpy as np

class Player:
    def __init__(self, name, bird_hand, food_supply, num_turns):
        self.name = name
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.num_turns = num_turns
        self.turns_remaining = num_turns
        self.game_board = GameBoard()
        self.score = 0
        self.actions = ["play_a_bird", "gain_food", "draw_a_bird"] # lay_eggs not implemented yet

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
    
    def _enumerate_legal_actions(self, tray, bird_deck):
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
            ## player must have a bird in hand
            birds_in_hand = self.bird_hand.get_cards_in_hand()
            if len(birds_in_hand) > 0:
                # player must have enough food to play a bird
                if any([self.food_supply.can_play_bird(bird) for bird in birds_in_hand]):
                    legal_actions.append(self.actions[0])
        
        # Player can always gain food
        legal_actions.append(self.actions[1])

        # Check if player can draw a bird
        if bird_deck.get_count() > 0 or tray.get_count() > 0:
            legal_actions.append(self.actions[2])

        return legal_actions
    
    def _choose_action(self, tray, bird_deck):
        '''
        Prompts the player to choose an action and returns the chosen action.

        Returns:
            chosen_action (str): The chosen action by the player.
        '''
        raise NotImplementedError

    def request_action(self, tray, bird_deck):
        '''
        Chooses an action to take based on the current game state and returns it.

        Args:
            tray (Tray): The bird tray.
            bird_deck (Deck): The bird deck.
        '''
        action = self._choose_action(tray=tray, bird_deck=bird_deck)
        return action
    
    def take_action(self, action, tray, bird_deck, bird_feeder):
        '''
        Takes an action based on the current game state.

        Args:
            action (str): The action to take.
            tray (Tray): The bird tray.
            bird_deck (Deck): The bird deck.
        '''
        if action not in self.actions:
            raise Exception(f"Action {action} is not valid.")
        elif action == self.actions[0]:
            self.play_a_bird()
        elif action == self.actions[1]:
            self.gain_food(bird_feeder)
        else:
            self.draw_a_bird(tray, bird_deck)

    def _choose_a_bird_to_play(self):
        '''
        Prompts the player to choose a bird from their hand.

        Returns:
            chosen_bird (str): The name of the chosen bird.
        '''
        raise NotImplementedError
    
    def play_a_bird(self):
        '''
        Player is prompted to choose a bird from their hand, and the bird is played to their game board.
        '''
        bird_name = self._choose_a_bird_to_play()
        food_cost = self.bird_hand.get_card(bird_name).get_food_cost()
        self.food_supply.decrement(food_cost)
        self.bird_hand.play_bird(bird_name, self.game_board)
    
    def gain_food(self, bird_feeder):
        '''
        Player gains food from the bird feeder.

        Args:
            bird_feeder (BirdFeeder): The bird feeder.
        '''
        # take one food at a time
        bird_feeder.take_food()
        self.food_supply.increment(1)

    def _choose_a_bird_to_draw(self, tray, bird_deck):
        '''
        Prompt the player to choose a bird to draw from either the bird deck or the tray.

        Args:
            tray (Tray): The tray object.
            bird_deck (BirdDeck): The bird deck object.

        Returns:
            chosen_bird (str): The name of the chosen bird, 'deck' if drawing from the deck.

        Raises:
            Exception: If both the bird deck and tray are empty.
        '''
        raise NotImplementedError

    def draw_a_bird(self, tray, bird_deck):
        chosen_bird = self._choose_a_bird_to_draw(tray, bird_deck)

        # Remove the bird from the tray or deck
        if chosen_bird == "deck":
            try:
                self.bird_hand.draw_card_from_deck(bird_deck)
                print(f"You drew {self.bird_hand.get_card_names_in_hand()[-1]} from the deck.")
            except Exception as e:
                # this should only happen if the deck is empty, but the user knows to type 'deck' in that case
                print(f"Error: {e}")
                chosen_bird = self._choose_a_bird_to_draw(tray, bird_deck)
        else:
            self.bird_hand.draw_bird_from_tray(tray, chosen_bird)

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
    def _choose_action(self, tray, bird_deck):
        '''
        Prompts the player to choose an action and returns the chosen action.

        Returns:
            chosen_action (str): The chosen action by the player.
        '''
        actions_map = {
            '1': self.actions[0],
            '2': self.actions[1],
            '3': self.actions[2]
        }
        legal_actions = self._enumerate_legal_actions(tray=tray, bird_deck=bird_deck)
        
        # Prompt the player to choose an action
        prompt = "Type 1 to play a bird, 2 to gain food, or 3 to draw a bird."
        chosen_action = input(prompt).strip()

        # Check if the chosen action is legal
        while actions_map[chosen_action] not in legal_actions:
            print(f"You are unable to {actions_map[chosen_action]}. {prompt}")
            chosen_action = input(prompt).strip()

        return actions_map[chosen_action]

    def _choose_a_bird_to_play(self):
        '''
        Prompts the player to choose a bird from their hand.

        Returns:
            chosen_bird (str): The name of the chosen bird.
        '''
        legal_birds_in_hand = [bird.get_name() for bird in self.bird_hand.get_cards_in_hand() if self.food_supply.can_play_bird(bird)]
        prompt = "Choose a bird to play: " + "\n" + "\n".join(legal_birds_in_hand) + "\n"
        chosen_bird = input(prompt)
        while chosen_bird not in self.bird_hand.get_card_names_in_hand():
            print(f"{chosen_bird} is not a valid bird. {prompt}")
            chosen_bird = input(prompt)

        return chosen_bird

    def _choose_a_bird_to_draw(self, tray, bird_deck):
        '''
        Prompt the player to choose a bird to draw from either the bird deck or the tray.

        Args:
            tray (Tray): The tray object.
            bird_deck (BirdDeck): The bird deck object.
            
        Returns:
            chosen_bird (str): The name of the chosen bird, 'deck' if drawing from the deck.

        Raises:
            Exception: If both the bird deck and tray are empty.
        '''
        # Check if the bird deck and/or tray are empty
        deck_is_empty = bird_deck.get_count() == 0
        tray_is_empty = tray.get_count() == 0

        # This shouldn't happen, since draw_a_bird won't be a legal action in this case.
        if deck_is_empty and tray_is_empty:
            raise Exception("The bird deck and tray are empty. Cannot draw a bird.")

        prompt_from_tray = "Choose a bird from the tray: " + "\n" +  "\n".join(tray.see_birds_in_tray())
        prompt_from_deck = "type 'deck' to draw from the bird deck."

        # If the tray is empty, draw from the bird deck
        if tray_is_empty:
            prompt = "The tray is empty, " + prompt_from_deck
        elif deck_is_empty:
            prompt = prompt_from_tray
        else:
            prompt = prompt_from_tray + "\nor " + prompt_from_deck

        # Prompt the player to choose a bird
        chosen_bird = input(prompt).strip()
        while chosen_bird not in tray.see_birds_in_tray() and chosen_bird != "deck":
            print(f"{chosen_bird} is not a valid bird.")
            chosen_bird = input(prompt).strip()

        return chosen_bird

class BotPlayer(Player):
    def __init__(self, policy=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        '''
        Args:
            policy (Policy): The policy to use for the bot. If None, a random policy will be used.
        '''
        if policy is None:
            self.policy = RandomPolicy()
        else:
            self.policy = policy  # Load learned policy here

    def _get_state(self, phase, tray=None, bird_deck=None, legal_actions=None):
        # Convert the current game state to a format that the policy can understand
        state = State(
            game_board=self.game_board,
            bird_hand=self.bird_hand,
            food_supply=self.food_supply,
            phase=phase,
            tray=tray,
            bird_deck=bird_deck,
            legal_actions=legal_actions
        )
        return state

    def _choose_action(self, tray, bird_deck):
        # enumerate the legal actions
        legal_actions = self._enumerate_legal_actions(tray=tray, bird_deck=bird_deck)

        # Convert the current game state to a format that the policy can understand
        state = self._get_state(phase='choose_action', tray=tray, bird_deck=bird_deck, legal_actions=legal_actions)

        # Use the policy to get the probabilities of each action
        action_probs = self.policy(state)

        # Choose an action according to the probabilities
        action_index = np.random.choice(len(action_probs), p=action_probs)
        action = legal_actions[action_index]

        return action

    def _choose_a_bird_to_play(self):
        # Convert the current game state to a format that the policy can understand
        state = self._get_state(phase='choose_a_bird_to_play')

        # Use the policy to get the probabilities of each action
        action_probs = self.policy(state)

        # Choose an action according to the probabilities
        action_index = np.random.choice(len(action_probs), p=action_probs)

        # Convert the action back to a bird
        birds_in_hand = self.bird_hand.get_card_names_in_hand()
        chosen_bird = birds_in_hand[action_index]

        return chosen_bird
        
    def _choose_a_bird_to_draw(self, tray, bird_deck):
        # Convert the current game state to a format that the policy can understand
        state = self._get_state(phase='choose_a_bird_to_draw', tray=tray, bird_deck=bird_deck)

        # Use the policy to get the probabilities of each action
        action_probs = self.policy(state)

        # Choose an action according to the probabilities
        action_index = np.random.choice(len(action_probs), p=action_probs)

        # Convert the action back to a bird
        choices = tray.see_birds_in_tray() + ["deck"]
        chosen_bird = choices[action_index]

        return chosen_bird