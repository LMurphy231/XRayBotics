from os import path

import numpy as np
import RobotCommunicator as com
import LightSensor as lightSensor
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths

def gravity_test_automated(x, y, z, freq=4500, Navg=4, threshold:float=0.75, step_length:int=1, length: float=100.0, width:float=100.0, angle:float=0.0, fr5=None):
    '''
    gravity_test_automated
    Perform the gravity test: Scan laser to find true 
    step_length in mm
    '''
    # New input: laser location: which side? left/right or above/below?
    # if left -> rotate 90 about current z0 (robot)
    
    # Return to "home" pos ---> isocenter+
    est_isocenter: np.ndarray = np.array([x, y, z])
    com._position_move(fr5, est_isocenter) # Start test at estimated isocenter ("origin")

    # Define data to collect
    grav_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    grav_test_pos_data: list = []    # Position Vectors (x,y,z)
    grav_test_light_data: list = []  # Light intensity values
            
    # Define path to move in (rectangle)
    grav_test_axes = ("y", "z") # Define active axes
    rectangle_points: list = paths.calculate_four_points_rectangle(est_isocenter, length, width, grav_test_axes[0], grav_test_axes[1])
    
    if angle != 0.0:
        rectangle_points = paths.rotate_points(rectangle_points, angle, grav_test_axes[0], grav_test_axes[1]) # Rotate if needed

    path: list = paths.rectangle_path(est_isocenter, rectangle_points) # Create path with points

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, grav_test_scan_data, step_length)
    # end_data_recording()
    
    # Return to "home" pos ---> isocenter
    com._position_move(fr5, est_isocenter) # End test at estimated isocenter ("origin")
    
    # Process scan data
    for scan_result in grav_test_scan_data:
        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        grav_test_pos_data.append(position)
        grav_test_light_data.append(light_intensity)
    
    #DataProcessing(grav_test_position_data, grav_test_light_data)

    return

def collimator_test_automated(x, y, z, freq=4500, Navg=4,threshold: float = 0.75, step_length: int = 1, 
                              length: float = 100.0, width: float = 100.0, angle: float = 0.0, fr5=None):
    '''
    collimator_test_automated
    Perform the Collimator Test: Scan laser to find true z
    '''

    # Return to "home" pos ---> isocenter
    est_isocenter: np.ndarray = np.array([x, y, z])
    com._position_move(fr5, est_isocenter)  # Start test at estimated isocenter ("origin")

    # Define data to collect
    coll_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    coll_test_pos_data: list = []    # Position Vectors (x,y,z)
    coll_test_light_data: list = []  # Light intensity values

    # Define path to move in (rectangle)
    coll_test_axes: tuple = ("x", "y")  # Define active axes
    rectangle_points: list = paths.calculate_four_points(est_isocenter, length, width, coll_test_axes[0], coll_test_axes[1])

    # Rotate rectangle if needed
    if angle != 0.0:
        rectangle_points = paths.rotate_points( rectangle_points, angle, coll_test_axes[0], coll_test_axes[1])

    # Create path with points
    path: list = paths.rectangle_path(est_isocenter, rectangle_points)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, coll_test_scan_data, step_length)
    # end_data_recording()

    # Return to "home" pos ---> isocenter
    com._position_move(fr5, est_isocenter)  # End test at estimated isocenter ("origin")

    # Process scan data
    for scan_result in coll_test_scan_data:
        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        coll_test_pos_data.append(position)
        coll_test_light_data.append(light_intensity)

    # DataProcessing(coll_test_pos_data, coll_test_light_data)

    return


def gantry_test_automated(x, y, z, freq=4500, Navg=4,threshold: float = 0.75, step_length: int = 1, 
                          length: float = 100.0,width: float = 100.0,angle: float = 0.0,fr5=None):
    '''
    gantry_test_automated
    Perform the Gantry Test: Scan laser to find true gantry position
    '''

    # Return to "home" pos ---> isocenter
    est_isocenter: np.ndarray = np.array([x, y, z])
    com._position_move(fr5, est_isocenter)  # Start test at estimated isocenter ("origin")

    # Define data to collect
    gantry_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    gantry_test_pos_data: list = []    # Position Vectors (x,y,z)
    gantry_test_light_data: list = []  # Light intensity values

    # Define path to move in (rectangle)
    gantry_test_axes: tuple = ("y", "z")  # Define active axes

    rectangle_points: list = paths.calculate_four_points(est_isocenter, length, width, gantry_test_axes[0], gantry_test_axes[1])

    # Rotate rectangle if needed
    if angle != 0.0:
        rectangle_points = paths.rotate_points(rectangle_points, angle, gantry_test_axes[0], gantry_test_axes[1])

    # Create path with points
    path: list = paths.rectangle_path(est_isocenter, rectangle_points)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, gantry_test_scan_data, step_length)
    # end_data_recording()

    # Return to "home" pos ---> isocenter
    com._position_move(fr5, est_isocenter)  # End test at estimated isocenter ("origin")

    # Process scan data
    for scan_result in gantry_test_scan_data:

        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        gantry_test_pos_data.append(position)
        gantry_test_light_data.append(light_intensity)

    # DataProcessing(gantry_test_pos_data, gantry_test_light_data)

    return