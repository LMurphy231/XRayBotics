from os import path

import numpy as np
import RobotCommunicator as com
import AutomatedTests.paths as paths
import LightSensor as lightSensor

def gravity_test_automated(fr5=None, x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100):

    # Return to "home" pos ---> isocenter
    # move(home) # Whatever this may be # TODO Estimated isocenter inputted by Sam!!!

    est_isocenter = np.array([0,0,0])
    com._position_move(fr5, est_isocenter) # Start test as estimated isocenter ("origin")

    # Define data to collect
    grav_test_light_data = []       # Light intensity values
    grav_test_position_data = []    # Position Vectors (x,y,z)

    # Define path to move in (rectangle)
    grav_test_axes = ["0", "y", "z"] # Gets changed internally
    path = paths.rectangle_path_center_referenced(grav_test_axes, step, length, width)
    
    # start_data_recording()

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

