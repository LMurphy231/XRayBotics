import numpy as np
import RobotCommunicator as RC

import LightSensor as lq

# TODO: Complete functions
def absolute_move_path(fr5: RC.RobotCom, path: list):
    """
    absolute move_path()
    Generic: perform each movement in a moveset
    HELPER FUNCTION: making move compatible with a defined path
    """
    for position in path:
        x: float = position[0]     # Extract x from moveset for that move
        y: float = position[1]     # Extract y from moveset for that move
        z: float = position[2]     # Extract z from moveset for that move

        # Pass in the destination point
        
        # Robot's/GUI move function here
        #fr5._position_move(x, y, z)     # Absolute Position
        print(f'Moving to {[x, y, z]}')
        event = fr5.move_position(x, y, z)     # Absolute Position

    return

def increment_move_and_scan(fr5: RC.RobotCom, ls: lq.SensorManager, path: list, start_position: np.ndarray, scan_data: list, Navg: int, step_length: float = 1.0):
    """
    move_and_path
    Move ---> scan AFTER the movement
    """

    light_intensity: float = 0.0  # Store light values
    current_position: np.ndarray  # Store position values

    current_position = start_position.copy()
    
    # Find moveset to increment
    for displacement in path:
    
        mag_displacement: float = np.linalg.norm(displacement) # Magnitude of displacement vector
        
        if mag_displacement == 0:
            continue # Check if not actually moving
        
        n_steps: int = int(np.ceil(mag_displacement / step_length)) # Number of steps to move (ceiling)
        #n_steps: int = int(mag_displacement // step_length) 
        
        movement: np.ndarray = displacement / n_steps # Movement for each step
        total_displacement = 0.0 
        for i in range(n_steps):
            
            dx: float = movement[0]     # Extract dx from moveset for that move
            dy: float = movement[1]     # Extract dy from moveset for that move
            dz: float = movement[2]     # Extract dz from moveset for that move
            
            fr5.move_increment(dx, dy, dz, vel=100.0, acc=100.0) # Vector Movement; robot gui funciton

            # Scan after movement
            light_intensity = light_scan(ls, Navg) # Scan after movement

            # Update current absolute position
            current_position = current_position + movement
            total_displacement += np.linalg.norm(movement)

            # Store scan data: corresponding position (absolute) & light intensity 
            store_data(scan_data, total_displacement, current_position, light_intensity)

def execute_path(fr5: RC.RobotCom, ls: lq.SensorManager, path: list, scan_data: list, Navg: int, step_length: float = 1.0):
    """
    execute_path()
    Execute each path in a rectangle (path).
    Determines whether to move only or move and scan.
    WRAPPER FUNCTION: choose if scanning after (incremental) move or not
    """

    for move, scan, start_pos in path:
        
        if scan:
            increment_move_and_scan(fr5, ls, move, start_pos, scan_data, Navg, step_length) # Scan if True

        else:
            absolute_move_path(fr5, move) # Move without scanning

    return

def store_data(scan_data: list, mag_displacement: float, position: np.ndarray, light_intensity: float):
    '''
    store_data
    Create list of detected light values with corresponding position
    '''
    scan_result: tuple = (position.copy(), mag_displacement, light_intensity)
    scan_data.append(scan_result)
    
    return

def light_scan(ls:lq.SensorManager, Navg: int = 5):
    # TEMP
    light_intensity: float  # Store light values
    _, light_intensity = ls.read(Navg) # Return an int (or similar)

    return light_intensity
    
