import math


class Node:
    """A node in the MCTS game tree, tracking visit count and total reward for UCB1."""

    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.num_visits = 0
        self.total_reward = 0

    def get_ucb1(self, c=1.4142):
        """Upper Confidence Bound: exploitation (avg reward) + exploration (under-visited bonus)."""
        if self.num_visits == 0:
            return float("inf")
        return self.total_reward / self.num_visits + c * math.sqrt(math.log(self.parent.num_visits) / self.num_visits)


class Edge:
    """A directed edge in the MCTS game tree connecting a parent node to a child via an action."""

    def __init__(self, parent, child, action):
        self.parent = parent
        self.child = child
        self.action = action
