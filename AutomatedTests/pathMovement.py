import numpy as np
#import RobotCommunicator as com

import labquest as lq

# TODO: Complete functions
def absolute_move_path(isocenter: np.ndarray, path: list):
    """
    absolute move_path()
    Generic: perform each movement in a moveset
    Helper Function: making move compatible with a defined path
    """
    for position in path:
        x: float = position[0]     # Extract x from moveset for that move
        y: float = position[1]     # Extract y from moveset for that move
        z: float = position[2]     # Extract z from moveset for that move

        # Pass in the destination point
        
        # Robot's/GUI move function here
        #fr5._position_move(dx, dy, dz)     # Absolute Position
        
    return

def increment_move_and_scan(isocenter: np.ndarray, path: list, light_data: list, pos_data: list, step_length: float = 1.0):
    """
    move_and_path
    Move ---> scan AFTER the movement
    """
    
    light_intensity: float  # Store light values
    position: np.ndarray     # Store position values
    
    # Find moveset to increment
    for displacement in path:
    
        mag_displacement: float = np.linalg.norm(displacement) # Magnitude of displacement vector
        
        if mag_displacement == 0:
            continue # Check if not actually moving
        
        n_steps: int = int(np.ceil(mag_displacement / step_length)) # Number of steps to move (ceiling)
        #n_steps: int = int(mag_displacement // step_length) 
        
        movement: np.ndarray = displacement / n_steps # Movement for each step
 
        for i in range(n_steps):
            
            dx: float = movement[0]     # Extract dx from moveset for that move
            dy: float = movement[1]     # Extract dy from moveset for that move
            dz: float = movement[2]     # Extract dz from moveset for that move
            
            # Robot's/GUI move function here
            #fr5._incriment_move(dx, dy, dz)        # Vector Movement

            # Scan after movement
            # t, ld = lq.read(avg_sample)
            # light_intensity = scan() # Return an int (or similar)

            # Store scan data: light intensity & corresponding position (absolute)
            #position = np.array([dx, dy, dz])
            
            store_data(light_data, pos_data, light_intensity, position) # Append data 

    return

def execute_path(isocenter: np.ndarray, path: list, light_data: list, pos_data: list, step_length: float = 1.0):
    """
    execute_path()
    Execute each path in a rectangle (path).
    Determines whether to move only or move and scan.
    Wrapper function to choose if scanning after move or not
    """

    for move, scan in path:
        
        if scan:
            increment_move_and_scan(isocenter, move, light_data, pos_data, step_length) # Scan if True

        else:
            absolute_move_path(isocenter, move) # Move without scanning

    return

def store_data(light_data: list, pos_data: list, light_intensity: float, position: np.ndarray):
    '''
    store_data
    Create list of detected light values with corresponding position
    '''
    
    light_data.append(light_intensity)
    pos_data.append(position)

    return

def scan():
    pass
    