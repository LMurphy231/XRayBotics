from os import path

import numpy as np
import RobotCommunicator as RC
import LightSensor as lightSensor
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths

def gravity_test_automated(fr5: RC.RobotCom, x: float, y: float, z: float, side: str, 
                           Navg: int = 4, step_length: float = 1.0, 
                           length: float = 100.0, width:float = 100.0):
    '''
    gravity_test_automated
    Perform the gravity test: Scan laser to find true z (gravity)
        Returns: offset for angle needed to adjust about an axis (X or Y) to align robot z-axis with true z-axis (gravity)
    step_length in mm
    ASSUMPTION: CCW is positive rotation about axis (right hand rule)
    ASSUMPTION: Photodiode will face the LINAC gantry (+x) in default pose 
    ASSUMPTIONS: Axis directions when facing gantry (default pose):
        +x: toward gantry <---> -x: away from gantry
        +y: left of gantry  <---> -y: right of gantry   
        +z: up  <---> -z: down
        
    np.eye(n): Create n x n identity matrix
    '''
    
    # ============================================================
    # START INITIALIZATION STATE: INITIALIZE DATA COLLECTION
    # ============================================================
    
    # Define variables and data to collect
    grav_rectangle_points: list = [] # Rectangle points or Gravity Test path points
    grav_path: list = [] # Path to move in (rectangle) for Gravity Test
    
    grav_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    grav_test_pos_data: list = []    # Position Vectors (x,y,z)
    grav_test_light_data: list = []  # Light intensity values
    
    grav_plane_angle: int = 0               # Angle to rotate rectangle points about z-axis to point photo-diode in +y-direction (left) or -y-direction (right)
    grav_rot_matrix: np.ndarray = np.eye(3) # Rotation matrix to rotate rectangle points about z-axis to point photo-diode in +y-direction (left) or -y-direction (right)
    grav_angle_offset: float = 0.0          # Offset angle to rotate rectangle points about z-axis to point photo-diode in +y-direction (left) or -y-direction (right)

    # ============================================================
    # END INITIALIZATION STATE: INITIALIZE DATA COLLECTION
    # ============================================================

    # ============================================================
    # START MOTION PLANNING STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, DEFINE MOVEMENT PATH
    # ============================================================
    
    # Return to "home" pos ---> isocenter+
    est_isocenter: np.ndarray = np.array([x, y, z])
    RC._position_move(fr5, est_isocenter) # Start test at estimated isocenter ("origin")

    # Define Basis Plane Rectangle: XY
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY
    basis_plane_path: list = paths.rectangle_path(est_isocenter, basis_points)                  # Create path with points in basis plane: XY

    # Rotate the robot to the correct side to ensure photodiode faces laser
    if side == "left":
        RC._rotate(fr5, axis = "z", angle = 90)   # if left -> rotate 90 about current z0 (robot)
        grav_plane_angle = 90 # Rotate rectangle points about z-axis to point photo-diode in +y-direction
    elif side == "right":
        RC._rotate(fr5, axis = "z", angle = -90)   # if right -> rotate -90 about current z0 (robot)
        grav_plane_angle = -90
    elif side == "front":
        grav_plane_angle = 0  # No rotation needed; laser already facing photodiode
              
    # Define new rectangle points and path for Gravity Test based on rotation of basis plane points          
    if grav_plane_angle != 0:
        # Rotate rectangle points about z-axis to point photo-diode in +/- y-direction
        grav_rot_matrix = paths.get_rotation_matrix("z", grav_plane_angle, grav_angle_offset) # Rotate about z-axis to point photo-diode in +/- y-direction
        grav_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)
        grav_path = paths.rectangle_path(est_isocenter, grav_rectangle_points)       
    else:
        grav_rectangle_points = basis_points    # No rotation needed; laser already facing photodiode
        grav_path = basis_plane_path            # No rotation needed; laser already facing photodiode
              
    # ============================================================
    # END MOTION PLANNING STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, DEFINE MOVEMENT PATH
    # ============================================================
    
            
            
    # ============================================================        
    # START CONTROL LOGIC: MOVE IN XZ ----> GET ANGLE ABOUT (WRT) Y AXIS
    # ===========================================================

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(fr5, grav_path, grav_test_scan_data, Navg, step_length) # Move and scan in path according
    # end_data_recording()
    
    # Return to "home" pos ---> isocenter
    RC._position_move(fr5, est_isocenter) # End test at estimated isocenter ("origin")
    
    # Process scan data
    for scan_result in grav_test_scan_data:
        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        grav_test_pos_data.append(position)
        grav_test_light_data.append(light_intensity)
    
    # Alan returns: offset for angle needed to adjust about Y
        #DataProcessing(grav_test_position_data, grav_test_light_data)
    
    dr_offset: float # STORE: ANGLE BETWEEN Y (TRUE) AND Z (ROBOT)
    # offset negative theta: CW
    
    if side == "left":
        fr5.offset_add("Gravity", dry = dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)    
    elif side == "right":
        fr5.offset_add("Gravity", drx = dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)  
    elif side == "front":
        pass
    
    # ex: angle btwn X and Z axis which represents offset about Y
    
    # Use previouslycalculated offsets to adjust robot rotation about X and Y axes to align robot z-axis with true z-axis (gravity)
    # TODO:
    
    # ============================================================        
    # END CONTROL LOGIC: MOVE IN XZ ----> GET ANGLE ABOUT (WRT) Y AXIS
    # ===========================================================
       
       
       
    # global value in robot.com to store offsets for both axes (X, Y, and Z) to adjust robot rotation
    
    # REPEAT IF NEEDED IF NOT WITHIN 0.1 DEGREES

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
    RC._position_move(fr5, est_isocenter)  # Start test at estimated isocenter ("origin")

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
    move.execute_path(fr5, path, coll_test_scan_data, Navg, step_length)
    # end_data_recording()

    # Return to "home" pos ---> isocenter
    RC._position_move(fr5, est_isocenter)  # End test at estimated isocenter ("origin")

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
    RC._position_move(fr5, est_isocenter)  # Start test at estimated isocenter ("origin")

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
    move.execute_path(fr5, path, gantry_test_scan_data, Navg, step_length)
    # end_data_recording()

    # Return to "home" pos ---> isocenter
    RC._position_move(fr5, est_isocenter)  # End test at estimated isocenter ("origin")

    # Process scan data
    for scan_result in gantry_test_scan_data:

        position: np.ndarray = scan_result[0]
        light_intensity: float = scan_result[1]

        gantry_test_pos_data.append(position)
        gantry_test_light_data.append(light_intensity)

    # DataProcessing(gantry_test_pos_data, gantry_test_light_data)

    return

'''
 offset_angle = 0 # Degrees
    gen_rot_matrix = paths.get_rotation_matrix("z", grav_rectangle_points, rot_angle, offset_angle) # Rotate about x-axis to point photo-diode in y-direction
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
'''
