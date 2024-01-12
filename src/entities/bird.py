class Bird:
    def __init__(self, common_name, points, food_cost):
        self.common_name = common_name
        self.points = points
        self.food_cost = food_cost

    def get_name(self):
        return self.common_name
    
    def get_points(self):
        return self.points
    
    def get_food_cost(self):
        return self.food_cost
    
    def activate(self):
        # Add code for activation behavior here
        pass
