import numpy as np
import RobotCommunicator as com

# (x,y,z): tuple ---> immutable: can't change
# [x,y,z]: list ---> mutable: can change

def straight_path(origin: np.ndarray, p1: np.ndarray, p2: np.ndarray, 
                  increment: int, path_type: str = "vector", debug: bool = False) -> list:
    """
    straight_path
    ex:
        increment = 5
        p1 = (1,2,3)
        p2 = (4,5,6)
    """

    moves: list = []                # Store movements into a list
    displacement: np.array          # Store the displacement vector
    movement: np.ndarray            # Store how much to move in each axis

    current_position: np.ndarray    # Store current location
    new_position: np.ndarray        # Store next/new location

    displacement = p2 - p1          # Find displacement vector
    movement = displacement / increment  # Find movement for each increment

    # Simulation
    if debug:
        straight_path_debug_data(p1, p2, increment, displacement, movement) # Debug

    current_position = p1.copy() # Start at p1

    # Create moveset
    for i in range(increment):
        
        new_position = current_position + movement  # Find new absolute position
        absolute_position = origin + new_position   # Vector position to absolute

        # Debug: Individual movement
        if debug:
            print(f"\n--- Move {i + 1} ---")
            print(f"Current position:     {current_position}")
            print(f"Next movement vector: {movement}")
            print(f"New position:         {new_position}")

        if path_type == "vector":
                moves.append(movement) # Store the moves as vectors

        elif path_type == "absolute":
            moves.append(absolute_position) # Store the moves as absolute positions

        else:
            raise ValueError("path_type must be either vector-based or absolute-based")

        current_position = new_position # Update current position; Debug
    
    return moves

def straight_path_debug_data(p1, p2, increment, displacement, movement):

    # Debug: Overall path information
    print("\n========== STRAIGHT PATH ==========")
    print(f"Start:        {p1}")
    print(f"End:          {p2}")
    print(f"Displacement: {displacement}")
    print(f"increments:        {increment}")
    print(f"Movement:     {movement}")

def straight_path_simulation():

    # Define starting and ending positions
    p1: np.ndarray = np.array([10, 20, 30])
    p2: np.ndarray = np.array([20, 40, 60])

    # Define number of movements
    increment: int = 5

    # Generate straight-path moveset
    path: list = straight_path(p1, p2, increment)

    # Debug: Print complete moveset
    print("========== MOVESET ==========")

    for i in range(len(path)):
        print(f"Move {i + 1}: {path[i]}")

    print("=============================")







# SELF-SIMULATION ONLY; FOR MARC'S SUBSYSTEM MEETING AND DOCUMENTATION
def main():

    straight_path_simulation()

if __name__ == "__main__":
    main()