import numpy as np
import RobotCommunicator as RC

import LightSensor as lq

import logging

move_logger = logging.getLogger('Moving')
scan_logger = logging.getLogger('Scanning')
data_logger = logging.getLogger('Data Storage')
path_logger = logging.getLogger('Path Movement')

# TODO: Complete functions
def absolute_move_path(fr5: RC.RobotCom, path: list):
    """
    absolute move_path()
    Generic: perform each movement in a moveset
    HELPER FUNCTION: making move compatible with a defined path
    """
    for position in path:
        x: float = position[0]
        y: float = position[1]
        z: float = position[2]

        # Robot's/GUI move function here
        print(f'Moving to {[x, y, z]}')
        event = fr5.move_position(x, y, z)     # Absolute Position

    return

def increment_move_and_scan(fr5: RC.RobotCom, ls: lq.SensorManager, path: list, start_position: np.ndarray, Navg: int, step_length: float = 1.0):
    """
    move_and_path
    Move ---> scan AFTER the movement
    """
    
    scan_data: list = []
    current_position: np.ndarray
    total_displacement: float = 0.0
    light_intensity: float = 0.0

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
            
            dx: float = movement[0]
            dy: float = movement[1]
            dz: float = movement[2]
            
            fr5.move_increment(dx, dy, dz) # Vector Movement; robot gui funciton
            light_intensity = light_scan(ls, Navg)

            # Update current absolute position
            current_position = current_position + movement
            total_displacement += np.linalg.norm(movement)
            
            move_logger.info(f'Step {i+1}/{n_steps}')
            scan_logger.info(f'Light Intensity: {light_intensity:.2f}')
            
            store_data(scan_data, current_position, total_displacement, light_intensity)
            
    return scan_data

def execute_path(fr5: RC.RobotCom, ls: lq.SensorManager, path: list, scan_data: list, Navg: int, step_length: float = 1.0):
    """
    execute_path()
    Execute each path in a rectangle (path).
    Determines whether to move only or move and scan.
    WRAPPER FUNCTION: choose if scanning after (incremental) move or not
    """
    scan_data_for_side: list # Store scan data (pos, displ, light) for just 1 side; for segmenting data

    for move, scan, start_pos in path:
        if scan:
            path_logger.info(f'Moving and scanning: {move} from {start_pos}')
            scan_data_for_side = increment_move_and_scan(fr5, ls, move, start_pos, Navg, step_length) 
            scan_data.append(scan_data_for_side)
        
        else:
            path_logger.info(f'Moving without scanning: {move} from {start_pos}')
            absolute_move_path(fr5, move) # Move without scanning

def store_data(scan_data: list, position: np.ndarray, mag_displacement: float, light_intensity: float):
    '''
    store_data
    Create list of detected light values with corresponding position
    '''
    
    data_logger.info(f'Storing data: Position: {position}, Displacement: {mag_displacement:.2f}mm')
    scan_result: tuple = (position.copy(), mag_displacement, light_intensity)
    scan_data.append(scan_result)

    return

def light_scan(ls:lq.SensorManager, Navg: int = 5):
    '''
    light_scan()
    Scan light intensity using the light sensor (LabQuest)
    Returns the light intensity value
    '''
    
    light_intensity: float
    _, light_intensity = ls.read(Navg)

    return light_intensity
    
