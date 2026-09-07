from os import path

import numpy as np
import RobotCommunicator as com
import AutomatedTests.paths as paths

#TODO ---> PSEUDOCODE for automated Gravity test
# Add more args
def gravity_test_automated(fr5=None, *args, x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100):

    # Return to "home" pos
        # move(home) # Whatever this may be
    
    # Define data to collect
        # grav_test_light_data[]
        # grav_test_position_data[] # (x,y,z)

    # Define path to move in (rectangle)
        # path = paths.rectangle_path(x,y,z, *args)
            # Defines path "moveset;" (x,y,z)
            # Defines max positions to prevent collisions

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

# Add more args
#TODO ---> PSEUDOCODE
def collimator_test_automated(fr5=None, x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100):
    #here
    return


# NOT ACTUAL IMPLEMENTATION - that's for Alan
# MOCK STRUCTURE PSEUDOCODE TO HELP WITH WRITING THE TEST LOGIC
class DataProcessing:
    
    def get_center_1(data):
        # Process data: 
            # center1 = (max + min)/2
            # Returns: (x,y,z) and light_intensity
        return 

    def get_center_2(data):
        # Process data: 
            # center2 = (max + min)/2
            # Returns: (x,y,z) and light_intensity
        return

    def get_offset(data):
        # Process data: 
            # offset = max - min
            # Returns offset as single value
        return
