from os import path

import numpy as np
import RobotCommunicator as RC
import LightSensor as lq
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths
import dataProcessing as dp

import logging

atl_logger = logging.getLogger('Automated Tests')
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
    gravity_test_automated()
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

    atl_logger.info('STARTING GRAVITY TEST AUTOMATED') 
    grav_path_points: list = []
    grav_path: list = []
    
    grav_test_scan_data: list = []   # [ [ [(x,y,z), d, l], [...] ] , [ [(x,y,z), d, l], [...] ] ] 
    
    dr_offset: float            # Store angle offset about an axis (not Z)
    peaks: tuple [int, int]     # Peaks from Data Processing
  
    atl_logger.info('MOVING TO ESTIMATED ISOCENTER')     
    est_isocenter: np.ndarray = np.array([x, y, z])

    

    # Get axis offsets found from previous tests.
    end_effector_z_angle = {
    'left' : 90,
    'right':-90,
    'front': 0,
    }
    fr5.set_end_effector_angle(0.0, 0.0, end_effector_z_angle[side])


    fr5.move_to_isocenter(False)

    grav_path_points = create_gravity_test_path_points(fr5, est_isocenter, length, width, side)
    grav_path = paths.zigzag_path(est_isocenter, grav_path_points)
    
    # Move the robot and scan in the defined path
    atl_logger.info('PERFORMING MOVEMENT AND SCAN IN PATH') 
    move.execute_path(fr5, ls, grav_path, grav_test_scan_data, Navg, step_length)
    fr5.move_to_isocenter(False)
    
    atl_logger.info('MOVEMENT COMPLETED, PROCESSING SCAN DATA')
    rx_offset, ry_offset, rz_offset = fr5.offset[3:]
    # STORE: ANGLE BETWEEN Z (TRUE) AND AXIS
    try:
        dr_offset, notable_data_3d, notable_data_2d, intensities = dp.calculate_angle(grav_test_scan_data, "gravity") # Offset negative theta: CW\
        
        atl_logger.info(f'GRAVITY TEST RESULTS: Offset angle about axis (CW): {dr_offset:.4f} degrees')
        
        if side == "left":
            dr_offset += rx_offset
            fr5.offset_add("Gravity", drx = -dr_offset)  # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)    
        elif side == "right":
            dr_offset -= rx_offset
            fr5.offset_add("Gravity", drx = dr_offset) # Store offset for angle needed to adjust about Y to align robot z-axis with true z-axis (gravity)  
        elif side == "front":
            fr5.offset_add("Gravity", dry = -dr_offset)  # Store offset for angle needed to adjust about x to align robot z-axis with true z-axis (gravity)  
    
    except BaseException as e:
        print(f'ERROR IN GRAVITY TEST: {e}')
    atl_logger.info('GRAVITY TEST AUTOMATED COMPLETED')
    return grav_test_scan_data#, dr_offset

def collimator_test_automated(fr5: RC.RobotCom, ls: lq.SensorManager, x: float, y: float, z: float, 
                              x1:float, x2:float, y1:float, y2:float, w_umbra: float = 1.0, l_umbra: float = 0.75,
                              Navg = 4, threshold: float = 0.75, step_length: float = 1.0, 
                              collimator_angle: float = 0.0, gantry_angle: float = 0.0, couch_angle: float = 0.0):
    '''
    collimator_test_automated()
    Perform the Collimator Test: Scan laser to find true z
    '''
    atl_logger.info('STARTING COLLIMATOR TEST AUTOMATED')
    coll_test_scan_data: list = []   # Tuple of both position data & light: (position, light)
    dr_offset: float            # Store angle offset about an axis (not Z)
    peaks: tuple [int, int]     # Peaks from Data Processing

    atl_logger.info('MOVING TO ESTIMATED ISOCENTER')
    est_isocenter: np.ndarray = np.array([x, y, z])

    drx, dry, drz = fr5.offset[3:]
    end_effector_direction = 90
    fr5.set_end_effector_angle(end_effector_direction, gantry_angle, 0.0)

    fr5.move_to_isocenter(False)

    collimator_path_points = create_collimator_test_path_points(fr5, est_isocenter, x1, x2, y1, y2,  w_umbra, l_umbra, gantry_angle, collimator_angle, couch_angle)
    #collimator_path = paths.rectangle_path(est_isocenter, collimator_path_points) 
    collimator_path = paths.zigzag_path(est_isocenter, collimator_path_points) 

    atl_logger.info('PERFORMING MOVEMENT AND SCAN IN PATH')
    move.execute_path(fr5, ls, collimator_path, coll_test_scan_data, Navg, step_length) # Move and scan in path according
    fr5.move_to_isocenter(False)
    atl_logger.info('MOVEMENT COMPLETED, PROCESSING SCAN DATA')

    try:
        dr_offset, notable_data_3d, notable_data_2d, intensities = dp.calculate_angle(coll_test_scan_data, "collimator") # Offset negative theta: CW\
        
        atl_logger.info(f'COLLIMATOR TEST RESULTS: Offset angle about axis (CW): {dr_offset:.4f} degrees')
        
        fr5.offset_add("collimator", drz = collimator_angle -  drz - dr_offset)  # Store offset for angle needed to adjust about x to align robot z-axis with true z-axis (gravity)  
    
    except BaseException as e:
        print(f'ERROR IN COLLIMATOR TEST: {e}')

    #dr_offset, peaks = dp.calculate_gravity_angle(coll_test_scan_data, "collimator") # Offset negative theta: CW
    #fr5.offset_add("Collimator", drz = dr_offset)
    
    return coll_test_scan_data#, dr_offset

def gantry_test_automated(fr5: RC.RobotCom, ls:lq.SensorManager, x, y, z, x1:float, x2:float, y1:float, y2:float, 
                          height: float = 0.0, w_umbra: float = 1.0, l_umbra: float = 0.75,
                          threshold: float= .75, step_length:float = 1.0,  Navg=4, 
                          collimator_angle:float=0.0, gantry_angle:float=0.0, couch_angle:float=0.0):
    '''
    gantry_test_automated
    Perform the Gantry Test: Scan laser to find true gantry position
    '''

    atl_logger.info('STARTING GANTRY TEST AUTOMATED')
    gantry_test_scan_data: list = []    # Tuple of both position data & light: (position, light)
    dr_offset: float                    # Store angle offset about an axis (not Z)
    peaks: tuple [int, int]             # Peaks from Data Processing

    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # Floats
    
    # Set end effector sensor to face upwards (base direction is forward)
    end_effector_direction: float = 90
    fr5.set_end_effector_angle(end_effector_direction, gantry_angle, 0.0)
    #fr5.set_end_effector_angle(end_effector_direction, gantry_angle + rx_offset, ry_offset, collimator_angle - couch_angle + rz_offset)
    
    atl_logger.info('MOVING TO ESTIMATED ISOCENTER')
    est_isocenter: np.ndarray = np.array([x, y, z])
    fr5.move_to_isocenter(False)

    end_effector_direction: float = 90
    gantry_path_points = create_gantry_test_path_points(fr5, est_isocenter, x1, x2, y1, y2, gantry_angle, collimator_angle, couch_angle, w_umbra, l_umbra, height)
    
    gantry_path = paths.zigzag_path(est_isocenter, gantry_path_points) 
    #gantry_path = paths.zigzag_path(est_isocenter, gantry_path_points) 

    atl_logger.info('PERFORMING MOVEMENT AND SCAN IN PATH')
    move.execute_path(fr5, ls, gantry_path, gantry_test_scan_data, Navg, step_length)
    fr5.move_to_isocenter(False)
        
    atl_logger.info('MOVEMENT COMPLETED, PROCESSING SCAN DATA')
    try:
        dr_offset, notable_data_3d, notable_data_2d, intensities = dp.calculate_angle(gantry_test_scan_data, "gantry") # Offset negative theta: CW\
        
        atl_logger.info(f'GRAVITY TEST RESULTS: Offset angle about axis (CW): {dr_offset:.4f} degrees')
        
        fr5.offset_add("gantry", dry = gantry_angle - dr_offset)  # Store offset for angle needed to adjust about x to align robot z-axis with true z-axis (gravity)  
        
    except BaseException as e:
        print(f'ERROR IN GANTRY TEST: {e}')
    
    atl_logger.info('GANTRY TEST AUTOMATED COMPLETED')
    return gantry_test_scan_data#, dr_offset, peaks

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


# ===================== CREATING PATH POINTS FOR EACH LINAC TEST =======================

def create_gravity_test_path_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                         length: float, width: float, side: str):
    
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)  # Calculate rectangle points in basis plane: XY        

    # Get axis offsets found from previous tests.
    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # floats
    
    grav_plane_angle: float
    grav_rot_matrix: np.ndarray
    grav_path_points: list = [] # OUTPUT OF THIS FUNCTION 
    
    # Helper matrices for rotations
    matrix_1: np.ndarray
    matrix_2: np.ndarray

    grav_plane_angle = {
        'left' : 90,
        'right':-90,
        'front': 0,
        }
    
    if side == "left" or side == "right":
        matrix_1 = paths.get_rotation_matrix("x", grav_plane_angle[side], 0.0)
        matrix_2 = paths.get_rotation_matrix("y", grav_plane_angle[side], 0.0)  
        matrix_3 = paths.get_rotation_matrix("z", 90                    , 0.0) 


        matrix_4 = paths.get_rotation_matrix("x", rx_offset, 0.0)
        matrix_5 = paths.get_rotation_matrix("y", ry_offset, 0.0)  
        matrix_6 = paths.get_rotation_matrix("z", rz_offset, 0.0) 
        
        offset_matrix = paths.rotation_matricies(matrix_4, matrix_5, matrix_6)
        #grav_rot_matrix = paths.rotation_matricies(matrix_2, matrix_1) # Original
        grav_rot_matrix = paths.rotation_matricies(offset_matrix, matrix_3, matrix_2, matrix_1)
        grav_path_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)
        
    elif side == "front":
        
        matrix_1 = paths.get_rotation_matrix("x", 0, 0.0)   
        matrix_2 = paths.get_rotation_matrix("y", grav_plane_angle[side], 0.0)
        matrix_3 = paths.get_rotation_matrix("z", 90, rz_offset)

        matrix_4 = paths.get_rotation_matrix("x", rx_offset, 0.0)
        matrix_5 = paths.get_rotation_matrix("y", ry_offset, 0.0)  
        matrix_6 = paths.get_rotation_matrix("z", rz_offset, 0.0)

        offset_matrix = paths.rotation_matricies(matrix_4, matrix_5, matrix_6)

        #grav_rot_matrix = paths.rotation_matricies(matrix_1, matrix_2)
        grav_rot_matrix = paths.rotation_matricies(offset_matrix, matrix_3, matrix_1, matrix_2)
        grav_path_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, grav_rot_matrix)

    return grav_path_points

def create_collimator_test_path_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                            x1: float, x2: float, y1: float, y2: float, w_umbra: float, l_umbra: float,
                                            gantry_angle: float, collimator_angle: float, couch_angle: float
                                            ):
    '''
    create_collimator_test_path_points()
    Create path points for collimator test
    
    '''
    collimator_path_points: list = [] # OUTPUT OF THIS FUNCTION
    collimator_rot_matrix: np.ndarray
    
    # Actual light field dimensions
    field_length: float = x1 + x2
    field_width: float = y1 + y2

    # Define path to move in based on extra umbras
    length: float = field_length + 2*w_umbra
    width: float = field_width - 2*l_umbra # abs(2*l_umbra-1)
    
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width)
    #basis_plane_path: list = paths.rectangle_path(est_isocenter, basis_points)

    # Get axis offsets found from previous tests.
    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # Floats
    
    # Set end effector sensor to face upwards (base direction is forward)
    #end_effector_direction: float = 90
    #fr5.set_end_effector_angle(end_effector_direction + gantry_angle + rx_offset,  ry_offset, collimator_angle - couch_angle + rz_offset)

    rx_matrix: np.ndarray = paths.get_rotation_matrix("x", 0.0, rx_offset)                     # Rotate path about x axis (Rotation about x axis to match with true z)
    ry_matrix: np.ndarray = paths.get_rotation_matrix("y", gantry_angle, ry_offset)                              # Rotate path about y axis (Rotation about y axis to match with true z)
    rz_matrix: np.ndarray = paths.get_rotation_matrix("z", collimator_angle - couch_angle, rz_offset)   # Rotate path about z axis (Rotation about z axis to match with couch angle)

    # Rotate about x0, Rotate about y0, rotate about x2, rotate about z3
    collimator_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rz_matrix)
    #collimator_rot_matrix: np.ndarray = paths.rotation_matricies(rx_matrix, ry_matrix, rx2_matrix, rz_matrix)

    collimator_path_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, collimator_rot_matrix)
    return collimator_path_points

def create_gantry_test_path_points(fr5: RC.RobotCom, est_isocenter: np.ndarray, 
                                        x1: float, x2: float, y1: float, y2: float, 
                                        gantry_angle: float, collimator_angle: float, couch_angle: float, 
                                        w_umbra: float = 1.0, l_umbra: float = 0.75, height: float = 0.0):
    '''
    create_gantry_test_path_points()
    CReate path points for gantry test
    '''
    gantry_path_points: list = [] # OUTPUT OF THIS FUNCTION
    gantry_rot_matrix: np.ndarray

    # Actual light field dimensions
    field_length: float = x1 + x2
    field_width: float = y1 + y2

    # Define path to move in based on extra umbras
    length: float = field_length + 2*w_umbra
    width: float = field_width - 2*l_umbra #* l_umbra #abs(2*l_umbra-1)

    #est_isocenter = est_isocenter + np.array([0.0, 0.0, y1+umbra/2])
    
    #basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, height, dy=height/2) # Liam's old code
    basis_points: list = paths.basis_plane_calculate_four_points(est_isocenter, length, width, dy=-height/2)

    # Get axis offsets found from previous tests
    rx_offset, ry_offset, rz_offset = fr5.offset[3:] # Floats

    # Set end effector sensor to face upwards (base direction is forward)
    #end_effector_direction: float = 90
    #fr5.set_end_effector_angle(end_effector_direction, gantry_angle, 0.0)
    #fr5.set_end_effector_angle(gantry_angle + rx_offset, end_effector_direction + ry_offset, collimator_angle - couch_angle + rz_offset)
    
    rx_matrix = paths.get_rotation_matrix("x", 0.0, rx_offset)                                       # Rotate path about x axis (Rotation about x axis to match with true z)
    ry_matrix = paths.get_rotation_matrix("y", gantry_angle, ry_offset)                              # Rotate path about y axis (Rotation about y axis to match with true z)
    rz_matrix = paths.get_rotation_matrix("z", collimator_angle - couch_angle, rz_offset)            # Rotate path about z axis (Rotation about z axis to match with couch angle)

    gantry_path_offset_matrix = paths.get_rotation_matrix("y", 90, 0.0)     # Rotate path about y axis (main rotation about gantry)
    gantry_path_offset_matrix2 = paths.get_rotation_matrix("x", 90, 0.0)    # Rotate path about x axis (main rotation about gantry)
    gantry_path_offset_matrix3 = paths.get_rotation_matrix("z", 90, 0.0)    # Rotate path about z axis (main rotation about gantry)

    # Rotate about x0, Rotate about y0, rotate about x0, rotate about y2, rotate about x2 (or something like that)
    gantry_rot_matrix = paths.rotation_matricies(rx_matrix, ry_matrix, rz_matrix, gantry_path_offset_matrix3, gantry_path_offset_matrix2, gantry_path_offset_matrix)

    gantry_path_points = paths.rotate_basis_plane_points(est_isocenter, basis_points, gantry_rot_matrix)

    return gantry_path_points

# ====================================================================================== 

# ===================== ROTATION MATRICES FOR EACH LINAC TEST ==========================

def gravity_test_rotation_matrix(grav_angle: float):
    return paths.rotation_matricies(paths.Ry(np.deg2rad(-90)), ) #TODO:

def collimator_test_rotation_matrix(col_angle, gan_angle):
    # start in YZ
    # rotate about y
    return paths.rotation_matrices(paths.Ry(np.deg2rad(-90)), )#TODO:

def gantry_test_rotation_matrix(gantry_angle, gan_angle):
    # start in YZ
    # rotate about y
    return paths.rotation_matricies(paths.Rx(np.deg2rad(-90)), )#TODO:

# =================================================================================  



def comments():
    
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




    #for position, distance, light_intensity in coll_test_scan_data:
#
    #    coll_test_pos_data.append(position)
    #    coll_test_distance.append(distance)
    #    coll_test_light_data.append(light_intensity)

    #dr_offset, peaks = dp.calculate_gravity_angle(coll_test_scan_data) # Offset negative theta: CW

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
    
    pass