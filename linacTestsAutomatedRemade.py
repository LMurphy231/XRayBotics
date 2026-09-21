from os import path

import numpy as np
import RobotCommunicator as com
import LightSensor as lightSensor
import AutomatedTests.pathMovement as move
import AutomatedTests.pathsRemade as paths

def gravity_test_automated(x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100, angle=0, fr5=None):
    '''
    gravity_test_automated
    Perform the gravity test: Scan laser to find true z
    '''
    # Return to "home" pos ---> isocenter
    est_isocenter = np.array([x, y, z])
    com._position_move(fr5, est_isocenter) # Start test as estimated isocenter ("origin"); by Sam

    # Define data to collect
    grav_test_light_data = []       # Light intensity values
    grav_test_position_data = []    # Position Vectors (x,y,z)
    
    # Define path to move in (rectangle)
    grav_test_axes = ("y", "z") # Define active axes
    rectangle_points = paths.calculate_four_points_trig(est_isocenter, length, width,angle, grav_test_axes[0], grav_test_axes[1])
    path = paths.rectangle_path(est_isocenter,rectangle_points, step)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, grav_test_light_data,  grav_test_position_data)
    # end_data_recording()






    # for direction_name, move_vec in path:
        # start.move(path)
            # scan light while moving
            # append.light_data[]                   # Store light intensity data
            # append.grav_test_position_data[]      # Store positional data (movement vectors)
            # tuple = append.[(dx,dy,dz), light_intensity]  # TODO: Tuple array possibly
        # end.move(path)
    
    # end_data_recording()
    
    # Process data (call needed DataProcessing.function() functions)
        # center1 = get_center_1(tuple)                     # Returns: (x,y,z) and light_intensity
        # center2 = get_center_2(tuple)                     # Returns: (x,y,z) and light_intensity
        # offset = get_offset(grav_test_position_data[])    # Returns offset 

    # Didn't find satisfactory light data
        # if (light_data < threshold)
            # path = paths.move_up_to_max_z(x,y,z, *args) # Move up to max z for a new path (different parameters)
            # start_data_recording()
                # start.move(path)
                    # scan light while moving
                    # append.light_data[]                   # Store light intensity data
                    # append.grav_test_position_data[]      # Store positional data (movement vectors)
                    # tuple = append.[(dx,dy,dz), light_intensity]  # TODO: Tuple array possibly
                # end.move(path)
            # end_data_recording()
    
    # Continue Here TODO


    return

def collimator_test_automated(x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100, angle=0, fr5=None):
    '''
    collimator_test_automated
    Perform the Collimator Test: Scan laser to find true z
    '''
    # Return to "home" pos ---> isocenter
    est_isocenter = np.array([x, y, z])
    com._position_move(fr5, est_isocenter) # Start test as estimated isocenter ("origin"); by Sam

    # Define data to collect
    coll_test_light_data = []       # Light intensity values
    coll_test_position_data = []    # Position Vectors (x,y,z)
    
    # Define path to move in (rectangle)
    coll_test_axes = ("x", "y") # Define active axes
    rectangle_points = paths.calculate_four_points_trig(est_isocenter, length, width,angle, coll_test_axes[0], coll_test_axes[1])
    path = paths.rectangle_path(est_isocenter, rectangle_points, step)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, coll_test_light_data,  coll_test_position_data)
    # end_data_recording()

    # Process the Data


def gantry_test_automated(x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100, angle=0, fr5=None):
    '''
    collimator_test_automated
    Perform the Collimator Test: Scan laser to find true z
    '''
    # Return to "home" pos ---> isocenter
    est_isocenter = np.array([x, y, z])
    com._position_move(fr5, est_isocenter) # Start test as estimated isocenter ("origin"); by Sam

    # Define data to collect
    gantry_test_light_data = []       # Light intensity values
    gantry_test_position_data = []    # Position Vectors (x,y,z)
    
    # Define path to move in (rectangle)
    gantry_test_axes = ("x", "y") # Define active axes
    rectangle_points = paths.calculate_four_points_trig(est_isocenter, length, width,angle, gantry_test_axes[0], gantry_test_axes[1])
    path = paths.rectangle_path(est_isocenter, rectangle_points, step)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, gantry_test_light_data,  gantry_test_position_data)
    # end_data_recording()

    # Process the Data