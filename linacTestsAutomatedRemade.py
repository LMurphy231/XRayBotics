from os import path

import numpy as np
import RobotCommunicator as RC
import LightSensor as lq
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths
import dataProcessingGravity as dp

import logging

atl_logger = logging.getLogger('Automated Test Logic Results')
atl_logger.setLevel(logging.INFO-1) # debug, info, warning, critical, error ---> low to high
logging.INFO # 20 is level for info; above is recorded
#atl_logger.propagate = False
    
'''
atl_logger.debug('Debug message')                   # logging.DEBUG     ---> 10
atl_logger.info('Application started')              # logging.INFO      ---> 20
atl_logger.warning('Disk space running low')        # logging.WARNING   ---> 30
atl_logger.error('Failed to connect to database')   # logging.ERROR     ---> 40
atl_logger.critical('System shutting down')         # logging.CRITICAL  ---> 50
'''

def gravity_test_automated(fr5: RC.RobotCom, ls: lq.SensorManager, x: float, y: float, z: float, side: str, 
                           Navg: int = 4, step_length: float = 0.5, 
                           length: float = 100.0, width:float = 100.0):
    '''
    gravity_test_automated
    Perform the gravity test: Scan laser to find true z (gravity)
        Returns: offset for angle needed to adjust about an axis (X or Y) to align robot z-axis with true z-axis (gravity)
    step_length in mm
    ASSUMPTION: 
        CCW is positive rotation about axis (right hand rule)
        CW is negative rotation about axis (right hand rule)
    ASSUMPTION: Photodiode will face the LINAC gantry (+x) in default pose 
    ASSUMPTIONS: Axis directions when facing gantry (default pose):
        +x: toward gantry <---> -x: away from gantry
        +y: left of gantry  <---> -y: right of gantry   
        +z: up  <---> -z: down
    
    scan_data: list[]  
        scan_data[0] = [(x1,y1,z1), (x2,y2,z3), ...] # List of np.ndarray for position
        scan_data[1] = [l1, l2, l3, ...] # List of floats for light intensity values
    
    np.eye(n): Create n x n identity matrix
    '''
    
    # ============================================================
    # START INITIALIZATION STATE: INITIALIZE DATA COLLECTION
    # ============================================================
    grav_rectangle_points: list = []
    grav_path: list = []
    
    grav_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    grav_test_pos_data: list = []    # List of position vectors (x,y,z) as np.ndarray
    grav_test_distance: list = []    # Distance from start of the current movement
    grav_test_light_data: list = [] 
    
    dr_offset: float # Store angle offset about an axis (not Z)

    # ============================================================
    # END INITIALIZATION STATE: INITIALIZE DATA COLLECTION
    # ============================================================



    # ============================================================
    # START MOTION PLANNING STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, DEFINE MOVEMENT PATH
    # ============================================================
        
    est_isocenter: np.ndarray = np.array([x, y, z])
    fr5._position_move(*est_isocenter) # Start/return to estimated isocenter ("origin")

    grav_rectangle_points = create_gravity_test_rectangle_points(fr5, est_isocenter, length, width, side)
    grav_path = paths.rectangle_path(est_isocenter, grav_rectangle_points)
    
    # ============================================================
    # END MOTION PLANNING STATE: ROTATE ROBOT TO CORRECT SIDE, RETURN TO ISOCENTER, DEFINE MOVEMENT PATH
    # ============================================================
    
            
            
    # ============================================================        
    # START CONTROL LOGIC: MOVE IN XZ ----> GET ANGLE ABOUT (WRT) Y AXIS
    # ===========================================================

    # Move the robot and scan in the defined path
    move.execute_path(fr5, ls, grav_path, grav_test_scan_data, Navg, step_length)
    fr5._position_move(*est_isocenter)
    
    # Process scan data
    for position, distance, light_intensity in grav_test_scan_data:
        grav_test_pos_data.append(position)
        grav_test_distance.append(distance)
        grav_test_light_data.append(light_intensity)

    return grav_test_scan_data


    #dr_offset, _ = dp.calculate_gravity_angle(grav_test_pos_data, grav_test_light_data) # STORE: ANGLE BETWEEN Z (TRUE) AND AXIS
    # offset negative theta: CW
    
    if side == "left":
        fr5.offset_add("Gravity", dry = dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)    
    elif side == "right":
        fr5.offset_add("Gravity", dry = -dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)  
    elif side == "front":
        fr5.offset_add("Gravity", drx = dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)  

    # Robot system: 
    
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
    # Create rotation matrix to adjust robot rotation about X and Y axes
    
   # Inform which test offset was from: gravity
   

    return

def collimator_test_automated(fr5: RC.RobotCom, ls: lq.SensorManager, x: float, y: float, z: float, 
                              x1:float, x2:float, y1:float, y2:float, umbra:float,
                              Navg=4, threshold: float = 0.75, step_length: float = 1.0, 
                              collimator_angle: float = 0.0, gantry_angle: float = 0.0, couch_angle: float = 0.0):
    '''
    collimator_test_automated
    Perform the Collimator Test: Scan laser to find true z
    '''

    # Return to "home" pos ---> isocenter
    est_isocenter: np.ndarray = np.array([x, y, z])
    fr5._position_move(*est_isocenter)  # Start test at estimated isocenter ("origin")

    # Define data to collect
    coll_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    coll_test_pos_data: list = []    # Position Vectors (x,y,z)
    coll_test_distance: list = []    # Distance from start of the current movement
    coll_test_light_data: list = []  # Light intensity values

    # Define path to move in (rectangle)
    #basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY
    ##basis_plane_path: list = paths.rectangle_path(est_isocenter, basis_points)                  # Create path with points in basis plane: XY
#
#
    # # Get axis offsets found from previous tests.
    #rx_offset, ry_offset, rz_offset = fr5.offset[3:]
    #
    ## Set end effector sensor to face upwards (base direction is forward)
    #end_effector_direction: float = 90
    #fr5.set_end_effector_angle(gantry_angle + rx_offset, end_effector_direction + ry_offset, collimator_angle + rz_offset)
    #
    ## Rotate path about x0 axis (Rotation about x axis to match with true z)
    #rx_matrix = paths.get_rotation_matrix("x", gantry_angle, rx_offset)
    #
    ## Rotate path about x axis (main rotation about gantry)
    #rx2_matrix = paths.get_rotation_matrix("x", gantry_angle, rx_offset)
#
    ## Rotate path about y axis (Rotation about y axis to match with true z)
    #ry_matrix = paths.get_rotation_matrix("y", 0.0, ry_offset)
#
    ## Rotate path about z axis (main rotation about collimator)
    #rz_matrix = paths.get_rotation_matrix("z", collimator_angle, rz_offset)
#
    ## Rotate about x0, Rotate about y0, rotate about x2, rotate about z3
    #grav_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rx2_matrix, rz_matrix)
#
    #collimator_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)
    collimator_rectangle_points = create_collimator_test_rectangle_points(fr5, est_isocenter, x1, x2, y1, y2, umbra, gantry_angle, collimator_angle, couch_angle)
    collimator_path = paths.rectangle_path(est_isocenter, collimator_rectangle_points) 

    move.execute_path(fr5, ls, collimator_path, coll_test_scan_data, Navg, step_length) # Move and scan in path according

    for position, distance, light_intensity in coll_test_scan_data:

        coll_test_pos_data.append(position)
        coll_test_distance.append(distance)
        coll_test_light_data.append(light_intensity)



    ## Rotate rectangle if needed
    #if angle != 0.0:
    #    rectangle_points = paths.rotate_points(rectangle_points, angle)
    #
    ## Create path with points
    #path: list = paths.rectangle_path(est_isocenter, rectangle_points)
    #
    ## Move the robot and scan in the defined path
    ## start_data_recording()
    #move.execute_path(fr5, path, coll_test_scan_data, Navg, step_length)
    ## end_data_recording()
    #
    ## Return to "home" pos ---> isocenter
    #fr5._position_move(*est_isocenter)  # End test at estimated isocenter ("origin")
    #
    ## Process scan data
    #for scan_result in coll_test_scan_data:
    #    position: np.ndarray = scan_result[0]
    #    light_intensity: float = scan_result[1]
    #
    #    coll_test_pos_data.append(position)
    #    coll_test_light_data.append(light_intensity)
    #
    ## DataProcessing(coll_test_pos_data, coll_test_light_data)

    return coll_test_scan_data


def gantry_test_automated(fr5: RC.RobotCom, ls:lq.SensorManager, x, y, z, x1:float, x2:float, y1:float, y2:float, height:float, umbra:float,
                          threshold: float= .75, step_length:float = 1.0,  Navg=4, 
                          collimator_angle:float=0.0, gantry_angle:float=0.0, couch_angle:float=0.0):
    '''
    gantry_test_automated
    Perform the Gantry Test: Scan laser to find true gantry position
    '''

    # Return to "home" pos ---> isocenter
    est_isocenter: np.ndarray = np.array([x, y, z])
    fr5._position_move(*est_isocenter)  # Start test at estimated isocenter ("origin")

    # Define data to collect
    gantry_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    gantry_test_pos_data: list = []    # Position Vectors (x,y,z)
    gantry_test_distance: list = []    # Distance from start of the current movement
    gantry_test_light_data: list = []  # Light intensity values

    # Define path to move in (rectangle)
    #basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY
    #basis_plane_path: list = paths.rectangle_path(est_isocenter, basis_points)                  # Create path with points in basis plane: XY
#
    ## Get axis offsets found from previous tests.
    #rx_offset, ry_offset, rz_offset = fr5.offset[3:]
#
    ## Set end effector sensor to face upwards (base direction is forward)
    #end_effector_direction: float = 90
    #fr5.set_end_effector_angle(gantry_angle + rx_offset, end_effector_direction + ry_offset, collimator_angle + rz_offset)
    #
    ## Rotate path about x0 axis (Rotation about x axis to match with true z)
    #rx_matrix = paths.get_rotation_matrix("x", gantry_angle, rx_offset)
    #
    ## Rotate path about x axis (main rotation about gantry)
    #rx2_matrix = paths.get_rotation_matrix("x", gantry_angle, rx_offset)
#
    ## Rotate path about y axis (Rotation about y axis to match with true z)
    #ry_matrix = paths.get_rotation_matrix("y", 0.0, ry_offset)
#
    ## Rotate path about z axis (main rotation about collimator)
    #rz_matrix = paths.get_rotation_matrix("z", collimator_angle, rz_offset)
#
    ## Rotate about x0, Rotate about y0, rotate about x2, rotate about z3
    #grav_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rx2_matrix, rz_matrix)
#
    #collimator_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)
    collimator_rectangle_points = create_gantry_test_rectangle_points(fr5, est_isocenter, x1, x2, y1, y2, height, umbra, gantry_angle, collimator_angle, couch_angle)
    collimator_path = paths.rectangle_path(est_isocenter, collimator_rectangle_points) 

    move.execute_path(fr5, ls, collimator_path, gantry_test_scan_data, Navg, step_length) # Move and scan in path according

    for position, distance, light_intensity in gantry_test_scan_data:

        gantry_test_pos_data.append(position)
        gantry_test_distance.append(distance)
        gantry_test_light_data.append(light_intensity)








    ## Define path to move in (rectangle)
    #gantry_test_axes: tuple = ("y", "z")  # Define active axes
    #
    #rectangle_points: list = paths.calculate_four_points(est_isocenter, length, width, gantry_test_axes[0], gantry_test_axes[1])
    #
    ## Rotate rectangle if needed
    #if angle != 0.0:
    #    rectangle_points = paths.rotate_points(rectangle_points, angle, gantry_test_axes[0], gantry_test_axes[1])
    #
    ## Create path with points
    #path: list = paths.rectangle_path(est_isocenter, rectangle_points)
    #
    ## Move the robot and scan in the defined path
    ## start_data_recording()
    #move.execute_path(fr5, path, gantry_test_scan_data, Navg, step_length)
    ## end_data_recording()
    #
    ## Return to "home" pos ---> isocenter
    #fr5.move(*est_isocenter)  # End test at estimated isocenter ("origin")
    #
    ## Process scan data
    #for scan_result in gantry_test_scan_data:
    #
    #    position: np.ndarray = scan_result[0]
    #    light_intensity: float = scan_result[1]
    #
    #    gantry_test_pos_data.append(position)
    #    gantry_test_light_data.append(light_intensity)

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


def create_gravity_test_rectangle_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                         length: float, width: float, side: str):
    
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY        

    # Get axis offsets found from previous tests.
    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # floats
    
    grav_plane_angle: float
    grav_rot_matrix: np.ndarray
    grav_rectangle_points: list = [] # OUTPUT OF THIS FUNCTION 
    
    # Helper matrices for rotations
    matrix_1: np.ndarray
    matrix_2: np.ndarray
    
    if side == "left":                  # Rotate basis place about x (CCW, +angle)
        grav_plane_angle = 90.0
        fr5.set_end_effector_angle(0.0, 0.0, grav_plane_angle)
             
    elif side == "right":               # Rotate basis place about x (CW, -angle)
        grav_plane_angle = -90.0
        fr5.set_end_effector_angle(0.0, 0.0, grav_plane_angle)
        
    elif side == "front":
        grav_plane_angle = 90.0
        fr5.set_end_effector_angle(0.0, 0.0, 0.0)

    if side == "left" or side == "right":
        matrix_1 = paths.get_rotation_matrix("x", grav_plane_angle, rx_offset)
        matrix_2 = paths.get_rotation_matrix("y", grav_plane_angle, ry_offset)   

        grav_rot_matrix = paths.rotation_matricies(matrix_2, matrix_1)
        grav_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)
        
    elif side == "front":
        
        matrix_1 = paths.get_rotation_matrix("x", 0, rx_offset)   
        matrix_2 = paths.get_rotation_matrix("y", grav_plane_angle, ry_offset)
        
        grav_rot_matrix = paths.rotation_matricies(matrix_1, matrix_2)
        grav_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)

    return grav_rectangle_points


def create_collimator_test_rectangle_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                            x1: float, x2: float, y1: float, y2: float, umbra: float, 
                                            gantry_angle: float, collimator_angle: float, couch_angle: float):

    collimator_rectangle_points: list = [] # OUTPUT OF THIS FUNCTION
    collimator_rot_matrix: np.ndarray

    length: float = x1 + x2 + umbra
    width: float = y1 + y2 - umbra
    
    # Define path to move in (rectangle)
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY
    #basis_plane_path: list = paths.rectangle_path(est_isocenter, basis_points)                  # Create path with points in basis plane: XY

    # Get axis offsets found from previous tests.
    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # Floats
    
    # Set end effector sensor to face upwards (base direction is forward)
    end_effector_direction: float = -90.0
    fr5.set_end_effector_angle(gantry_angle + rx_offset, end_effector_direction + ry_offset, collimator_angle - couch_angle + rz_offset)

    
    rx_matrix: np.ndarray = paths.get_rotation_matrix("x", gantry_angle, rx_offset)                     # Rotate path about x axis (Rotation about x axis to match with true z)
    ry_matrix: np.ndarray = paths.get_rotation_matrix("y", 0.0, ry_offset)                              # Rotate path about y axis (Rotation about y axis to match with true z)
    rz_matrix: np.ndarray = paths.get_rotation_matrix("z", collimator_angle - couch_angle, rz_offset)   # Rotate path about z axis (Rotation about z axis to match with couch angle)

    ## Rotate path about x0 axis (Rotation about x axis to match with true z)
    #rx_matrix = paths.get_rotation_matrix("x", 0.0, rx_offset)
    #
    ## Rotate path about x axis (main rotation about gantry)
    #rx2_matrix = paths.get_rotation_matrix("x", gantry_angle, 0.0)
#
    ## Rotate path about y axis (Rotation about y axis to match with true z)
    #ry_matrix = paths.get_rotation_matrix("y", 0.0, ry_offset)
#
    ## Rotate path about z axis (main rotation about collimator)
    #rz_matrix = paths.get_rotation_matrix("z", collimator_angle, rz_offset)

    # Rotate about x0, Rotate about y0, rotate about x2, rotate about z3
    collimator_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rz_matrix)
    #collimator_rot_matrix: np.ndarray = paths.rotation_matricies(rx_matrix, ry_matrix, rx2_matrix, rz_matrix)

    collimator_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, collimator_rot_matrix)
    return collimator_rectangle_points


def create_gantry_test_rectangle_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                        x1: float, x2: float, y1: float, y2: float, height: float, umbra: float, 
                                        gantry_angle: float, collimator_angle: float, couch_angle: float):

    gantry_rectangle_points: list = [] # OUTPUT OF THIS FUNCTION
    gantry_rot_matrix: np.ndarray

    length: float = x1 + x2 + umbra
    #height: float = y1 + y2 + umbra

    #est_isocenter = est_isocenter + np.array([0.0, 0.0, y1+umbra/2])

    # Define path to move in (rectangle)
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, height, dy=height/2)  # Calculate rectangle points in basis plane: XY

    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # Get axis offsets found from previous tests

    # Set end effector sensor to face upwards (base direction is forward)
    end_effector_direction: float = -90
    fr5.set_end_effector_angle(gantry_angle + rx_offset, end_effector_direction + ry_offset, collimator_angle - couch_angle + rz_offset)
    
    rx_matrix = paths.get_rotation_matrix("x", gantry_angle, rx_offset)                     # Rotate path about x axis (Rotation about x axis to match with true z)
    ry_matrix = paths.get_rotation_matrix("y", 0.0, ry_offset)                              # Rotate path about y axis (Rotation about y axis to match with true z)
    rz_matrix = paths.get_rotation_matrix("z", collimator_angle - couch_angle, rz_offset)   # Rotate path about z axis (Rotation about z axis to match with couch angle)

    gantry_path_offset_matrix = paths.get_rotation_matrix("y", 90, 0.0)     # Rotate path about y axis (main rotation about gantry)
    gantry_path_offset_matrix2 = paths.get_rotation_matrix("x", 90, 0.0)    # Rotate path about x axis (main rotation about gantry)
    gantry_path_offset_matrix3 = paths.get_rotation_matrix("z", 90, 0.0)    # Rotate path about z axis (main rotation about gantry)

    # Rotate about x0, Rotate about y0, rotate about x0, rotate about y2, rotate about x2 (or something like that)
    gantry_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rz_matrix, gantry_path_offset_matrix3, gantry_path_offset_matrix2, gantry_path_offset_matrix)

    gantry_rectangle_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, gantry_rot_matrix)

    return gantry_rectangle_points