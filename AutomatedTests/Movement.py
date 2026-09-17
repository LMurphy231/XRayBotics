import numpy as np
import RobotCommunicator as com

def move_in_absolute_path(path: list):
    """
    move_in_vector_path
    Interpret as (x,y,z): absolute positions relative to defined "origin" (isocenter)
    """
    for movement in path:
        x = 4
        # move(movement)    # Move robot to ABSOLUTE position
        # scan()            # Take light data AFTER moving
    
    return

def move_in_vector_path(path: list):
    """
    move_in_vector_path
    Interpret as: (dx,dy,dz) vectors (displacement from current location)
    """
    for movement in path:
        x = 4
        # move(movement)    # Move robot to RELATIVE/VECTOR position
        # scan()
        
    return