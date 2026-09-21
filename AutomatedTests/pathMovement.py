import numpy as np
import RobotCommunicator as com

# TODO: Complete functions

def move_path(path: list):
    """
    move_path()
    Generic: perform each movement in a moveset
    Helper Function: making move compatible with a defined path
    """
    for movement in path:
        dx: float = movement[0]     # Extract dx from moveset for that move
        dy: float = movement[1]     # Extract dy from moveset for that move
        dz: float = movement[2]     # Extract dz from moveset for that move

        # Robot's/GUI move function here; vectors or absolute posion?
        #fr5._incriment_move(10, 20, 30)
        #fr5._position_move(dx, dy, dz)
        
    return

def move_and_scan(path: list, light_data: list, pos_data: list):
    """
    move_and_path
    Move ---> scan AFTER the movement
    """
    light_intensity: float  # Store light values
    position: np.darray     # Store position values
    
    for movement in path:
        #move(movement)
        # light_intensity = scan() # Return an int (or similar)
        position = movement
        store_data(light_data, pos_data, light_intensity, position) # Store light intensity and mcorresponding position
        
    return

def store_data(light_data: list, pos_data: list, light_intensity: float, position: np.ndarray):
    # Create list of detected light values with corresponding position
    light_data.append(light_intensity)
    pos_data.append(position)
    return

def calculate_points():

    return