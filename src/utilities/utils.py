# utils.py

def render_bird_container(bird_container, capacity=None):
    '''
    Render a bird container.
    Examples are a bird hand, the bird tray, or a game board
    
    Args:
        bird_container (list[Bird]): The bird container to render.
        capacity (int): The capacity of the bird container.
    '''
    # set the capacity to the length of the bird container if no capacity is provided
    if capacity is None:
        capacity = len(bird_container)

    output = "{:<30s}{:<15s}{:<10s}\n".format("Bird Name", "Point Value", "Food Cost")
    for bird in bird_container:
        output += "{:<30s}{:<15d}{:<10d}\n".format(bird.get_name(), bird.get_points(), bird.get_food_cost())
    
    # this will only execute if empty slots should be rendered, for example a GameBoard that isn't full
    for _ in range(len(bird_container), capacity):
        output += "{:<30s}{:<15s}{:<10s}\n".format("empty", "--", "--")
    return output