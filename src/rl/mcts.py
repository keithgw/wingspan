import math

class Node():
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.num_visits = 0
        self.total_reward = 0
        self.untried_actions = state.get_legal_actions()
    
    def is_fully_expanded(self):
        return len(self.untried_actions) == 0
    
    def is_terminal(self):
        return self.state.is_terminal()
    
    def get_ucb1(self, c=1.4142):
        if self.num_visits == 0:
            return float('inf')
        else:
            return self.total_reward / self.num_visits + c * math.sqrt(math.log(self.parent.num_visits) / self.num_visits)
        
class Edge():
    def __init__(self, parent, child, action):
        self.parent = parent
        self.child = child
        self.action = action