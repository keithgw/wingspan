from src.entities.gameboard import GameBoard

class Player:
    def __init__(self, name, bird_hand, food_supply, num_turns):
        self.name = name
        self.bird_hand = bird_hand
        self.food_supply = food_supply
        self.num_turns = num_turns
        self.turns_remaining = num_turns
        self.game_board = GameBoard()
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
        birds_in_hand = self.bird_hand.get_cards_in_hand()
        #TODO: check that the game board is not full
        if len(birds_in_hand) > 0:
            # Check if player has enough food to play a bird
            if any([self.food_supply.can_play_bird(bird) for bird in birds_in_hand]):
                legal_actions.append(self.actions[0])
        
        # Player can always gain food
        legal_actions.append(self.actions[1])

        # Check if player can draw a bird
        if bird_deck.get_count() > 0 or tray.get_count() > 0:
            legal_actions.append(self.actions[2])

        return legal_actions
    
    def _choose_action(self, tray, bird_deck):
        actions_map = {
            1: self.actions[0],
            2: self.actions[1],
            3: self.actions[2]
        }
        legal_actions = self._enumerate_legal_actions(tray=tray, bird_deck=bird_deck)
        
        # Display legal_actions to the console
        prompt = "Type 1 to play a bird, 2 to gain food, or 3 to draw a bird."
        print(prompt)

        # Prompt the player to choose an action
        chosen_action = input("Choose an action: ")

        # Check if the chosen action is legal
        while chosen_action not in [1, 2, 3]:
            print(f"{chosen_action} is not vaild. {prompt}")
            print("Choose an action: ")
        while actions_map[chosen_action] not in legal_actions:
            print(f"You are unable to {actions_map[chosen_action]}. {prompt}")
            chosen_action = input("Choose an action: ")

        return actions_map[chosen_action]

    def request_action(self, tray, bird_deck):
        '''
        Chooses an action to take based on the current game state and returns it.

        Args:
            tray (Tray): The bird tray.
            bird_deck (Deck): The bird deck.
        '''
        action = self._choose_action(tray=tray, bird_deck=bird_deck)
        return action

    def choose_a_bird(self):
        '''
        Prompts the player to choose a bird from their hand.
        '''
        legal_birds_in_hand = [bird.get_name() for bird in self.bird_hand.get_cards_in_hand() if self.food_supply.can_play_bird(bird)]
        prompt = "Choose a bird to play: ".join([f"\n{bird}" for bird in legal_birds_in_hand])
        chosen_bird = input(prompt)
        while chosen_bird not in self.bird_hand.get_card_names_in_hand():
            print(f"{chosen_bird} is not a valid bird. {prompt}")
            chosen_bird = input(prompt)

        return chosen_bird
    
    def play_a_bird(self, bird_name):
        '''
        Player plays a bird to the game board.

        Args:
            bird_name (str): The name of the bird to play.
        '''
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

    def draw_bird(self, bird_deck, tray):
        '''
        Prompts the player to choose a bird from the bird deck or the tray.
        
        Args:
            bird_deck (Deck): The bird deck.
            tray (Tray): The bird tray.
        '''
        # Check if the bird deck and/or tray are empty
        deck_is_empty = bird_deck.get_count() == 0
        tray_is_empty = tray.get_count() == 0
        
        # If the tray is empty, draw from the bird deck
        prompt_from_tray = "Choose a bird: ".join([f"\n{bird}" for bird in tray.see_birds_in_tray()])
        prompt_from_deck = "type 'deck' to draw from the bird deck."
        if tray_is_empty:
            if deck_is_empty:
                pass #TODO: Handle empty deck and tray
            else:
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

        # Remove the bird from the tray or deck
        if chosen_bird == "deck":
            try:
                self.bird_hand.draw_card_from_deck(bird_deck)
                print(f"You drew {self.bird_hand.get_card_names_in_hand()[-1]} from the deck.")
            except Exception as e:
                # this should only happen if the deck is empty, but the user knows to type 'deck' in that case
                print(f"Error: {e}")
                chosen_bird = input(prompt).strip()
                while chosen_bird not in tray.see_birds_in_tray():
                    print(f"{chosen_bird} is not a valid bird.")
                    chosen_bird = input(prompt).strip()
        else:
            self.bird_hand.draw_bird_from_tray(tray, chosen_bird)
            
    def end_turn(self):
        '''
        Ends the player's turn.
        '''
        self.turns_remaining -= 1

    def get_turns_remaining(self):
        '''
        Returns the number of turns remaining for the player.
        '''
        return self.turns_remaining

