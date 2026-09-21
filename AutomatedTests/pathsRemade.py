import numpy as np
import RobotCommunicator as com

# (x,y,z): tuple ---> immutable: can't change
# [x,y,z]: list ---> mutable: can change

def straight_path(p1: np.ndarray, p2: np.ndarray, increment: int, discrete: bool = False) -> list:
    """
    straight_path()
    Return a move list that stores the straight path
    Incremental or non-incremental
    ex:
        increment = 5
        p1 = (1,2,3)
        p2 = (4,5,6)
    """

    moves: list = []                # Store movements into a list
    displacement: np.ndarray        # Store the displacement vector
    movement: np.ndarray            # Store how much to move in each axis
    
    displacement = p2 - p1          # Find displacement vector

    # Create moveset
    if discrete:
        # Find movement for each increment too
        movement = displacement / increment     
        for i in range(increment):         
            moves.append(movement)
        return moves  
    else:
        # Create moveset to record the path to move robot in
        movement = displacement
        moves.append(movement)
        return moves

def rectangle_path():
    return