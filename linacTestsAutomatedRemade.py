from os import path

import numpy as np
import RobotCommunicator as com
import LightSensor as lightSensor
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths

def gravity_test_automated(x, y, z, fr5=com.RobotCom, Navg=4, 
                           step_length:int=1, length: float=100.0, width:float=100.0, 
                           side: str ="left"):
    '''
    gravity_test_automated
    Perform the gravity test: Scan laser to find true 
    step_length in mm
    '''
    
    # ============================================================
    # INITIALIZATION STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, INITIALIZE DATA COLLECTION
    # ============================================================
    
    # Rotate the robot to the correct side to scan lase (left or right side)
    if side == "left":
        com._rotate(fr5, axis = "z", angle = 90)   # if left -> rotate 90 about current z0 (robot)
    elif side == "right":
        com._rotate(fr5, axis = "z", angle = -90)   # if right -> rotate -90 about current z0 (robot)
                
    # Return to "home" pos ---> isocenter+
    est_isocenter: np.ndarray = np.array([x, y, z])
    com._position_move(fr5, est_isocenter) # Start test at estimated isocenter ("origin")

    # Define data to collect
    grav_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    grav_test_pos_data: list = []    # Position Vectors (x,y,z)
    grav_test_light_data: list = []  # Light intensity values
            
    # ============================================================       
    # END INITIALIZATION STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, INITIALIZE DATA COLLECTION        
    # ============================================================        
            
            
            
    # ============================================================        
    # PROCEDURE 1: MOVE IN XZ ----> GET ANGLE ABOUT (WRT) Y AXIS
    # ===========================================================

    # Define path to move in (rectangle)
    grav_rectangle_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width) # Calculate rectangle points in basis plane: XZ
    
    # CURRENT ASSUMPTION: NO OTHER PLANE ROTATION NEEDED BEFORE SCANNING
        # Otherwise, would need to rotate rectangle points about axis to point photo-diode laser direction
    
    path: list = paths.rectangle_path(est_isocenter, grav_rectangle_points) # Create path with points

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, grav_test_scan_data, step_length) # Move and scan in path according
    # end_data_recording()
    
    # Return to "home" pos ---> isocenter
    com._position_move(fr5, est_isocenter) # End test at estimated isocenter ("origin")
    
    # Process scan data
    for scan_result in grav_test_scan_data:
        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        grav_test_pos_data.append(position)
        grav_test_light_data.append(light_intensity)
    
   
    # Alan returns: offset for angle needed to adjust about Y
        #DataProcessing(grav_test_position_data, grav_test_light_data)
    
    dry: float # STORE: ANGLE BETWEEN Y (TRUE) AND Z (ROBOT)

    # TODO:
    
    # ============================================================        
    # END PROCEDURE 1: MOVE IN XZ ----> GET ANGLE ABOUT (WRT) Y AXIS
    # ===========================================================
        
    
    
    # ============================================================
    # PROCEDURE 2: MOVE IN YZ ----> ANGLE ABOUT (WRT) X AXIS
    # ============================================================
    
    gen_rot_matrix = paths.get_rotation_matrix("z", grav_rectangle_points, 90, 0) # Rotate about x-axis to point photo-diode in y-direction
    grav_rotated_points: list = paths.rotate_points_basis_plane(grav_rectangle_points, gen_rot_matrix) # Rotate points in basis plane
    rotated_path: list = paths.rectangle_path(est_isocenter, grav_rotated_points) # Create rotated path with rotated points
    
    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(rotated_path, grav_test_scan_data, step_length) # Move and scan in rotated path accordingly
    # end_data_recording()
    
    # Return to "home" pos ---> isocenter
    com._position_move(fr5, est_isocenter) # End test at estimated isocenter ("origin")
    
    # Process scan data
    for scan_result in grav_test_scan_data:
        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        grav_test_pos_data.append(position)
        grav_test_light_data.append(light_intensity)

    # Alan returns: offset for angle needed to adjust about Y
        #DataProcessing(grav_test_position_data, grav_test_light_data)
    
    drx: float # STORE: ANGLE BETWEEN X (TRUE) AND Z (ROBOT)

    # ============================================================        
    # END PROCEDURE 2: MOVE IN YZ ----> ANGLE ABOUT (WRT) X AXIS
    # ===========================================================



    # ============================================================        
    # FINALIZATION: RETURN ANGLE OFFSETS FOR BOTH AXES (X AND Y) TO ADJUST ROBOT ROTATION
    # ===========================================================

    # GOAL: ALIGN ROBOT Z AXIS WITH TRUE Z AXIS (GRAVITY)
    offset: list = [np.ndarray([drx, dry])] # Return offset for both axes (X and Y) to adjust robot rotation
    # Create rotation matrix to adjust robot rotation about X and Y axes
    
   # Inform which test offset was from: gravity

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