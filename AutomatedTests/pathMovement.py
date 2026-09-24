import numpy as np
#import RobotCommunicator as com

# TODO: Complete functions

def move_path(path: list):
    """
    move_path()
    Generic: perform each movement in a moveset
    Helper Function: making move compatible with a defined path
    """
    for movement in path:
        x: float = movement[0]     # Extract x from moveset for that move
        y: float = movement[1]     # Extract y from moveset for that move
        z: float = movement[2]     # Extract z from moveset for that move

        # Pass in the destination point
        
        # Robot's/GUI move function here
        #fr5._position_move(dx, dy, dz)     # Absolute Position
        
    return

def increment_move_and_scan(path: list, light_data: list, pos_data: list):
    """
    move_and_path
    Move ---> scan AFTER the movement
    """
    
    light_intensity: float  # Store light values
    position: np.darray     # Store position values
    
    # Find movement for each increment too
    movement = displacement / (mag_displacement / step_length)    
    
    for movement in path:
        dx: float = movement[0]     # Extract dx from moveset for that move
        dy: float = movement[1]     # Extract dy from moveset for that move
        dz: float = movement[2]     # Extract dz from moveset for that move
        
        n_steps: int = int(mag_displacement // step_length)  
        movement = displacement / n_steps
        #movement = displacement / step_length  
        
        
        
        # Robot's/GUI move function here
        #fr5._incriment_move(dx, dy, dz)        # Vector Movement

        # Scan after movement
        # light_intensity = scan() # Return an int (or similar)

        # Store scan data: light intensity & corresponding position
        position: np.ndarray = np.array([dx, dy, dz])
        #position = movement
        store_data(light_data, pos_data, light_intensity, position) 

    return

def execute_path(rectangle_paths: list, light_data: list, pos_data: list):
    """
    execute_path()
    Execute each path in a rectangle (path).
    Determines whether to move only or move and scan.
    """

    for path, scan in rectangle_paths:

        if scan:
            move_and_scan(path, light_data, pos_data) # Scan if True

        else:
            move_path(path) # Move without scanning

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
    