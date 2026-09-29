import numpy as np
#import RobotCommunicator as com
#from LightSensor import SensorManager

# (x,y,z): tuple ---> immutable: can't change
# [x,y,z]: list ---> mutable: can change

def straight_path(p1: np.ndarray, p2: np.ndarray) -> list:
    """
    straight_path()
    Return a move list that stores the straight path
    Returns Vector/displacement between 2 points, not absolute position
    ex:
        p1 = (1, 2, 3)
        p2 = (2, 4, 6)
        movement = (1, 2, 3)
    """

    movement: list = []                # Store movements into a list
    displacement: np.ndarray        # Store the displacement vector
    movement: np.ndarray            # Store how much to move in each axis
    
    displacement = p2  - p1        # Find Magnitude displacement vector
  
    # Create moveset:  one movement for entire path from p1 to p2 without increments
    movement.append(displacement)
    return movement
    
def rectangle_path(isocenter: np.ndarray, points: list):
    """
    rectangle_path()
    Create the movement paths needed to travel around a rectangle.
    Returns movement vectors between the paths
    Movement:
        Isocenter -> P1       No scan
        P1 -> P2              Scan
        P2 -> P3              No scan
        P3 -> P4              Scan
    """

    # Access the 4 rectangle points; Class is drarray
    p1: np.ndarray = points[0]
    p2: np.ndarray = points[1]
    p3: np.ndarray = points[2]
    p4: np.ndarray = points[3]

    # Create paths for each side; Decided internally
    path_to_p1:     list = straight_path(isocenter, p1)   # Non-Incremental
    path_p1_to_p2:  list = straight_path(p1, p2)           # Incremental
    path_p2_to_p3:  list = straight_path(p2, p3)          # Non-Incremental
    path_p3_to_p4:  list = straight_path(p3, p4)           # Incremental

    # Store paths with scan information; True/False for Scanning
    rectangle_paths: list[tuple[list[np.ndarray], bool]]= [
        (path_to_p1, False),
        (path_p1_to_p2, True),
        (path_p2_to_p3, False),
        (path_p3_to_p4, True)
    ]

    return rectangle_paths





def calculate_four_points_(isocenter: np.ndarray, length: float, width: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_matrix
    Find the "4 corners" of the rectangle given L, W, angle, and active axes
    Center will be user-defined "isocenter" (origin)
    
    If isoceneter = (0,0,0) -> pointsa are both abs pos and displacement
    If isoceneter != (0,0,0) -> points are only abs pos
    
    Valid axis combinations:
        X, Y -> Rectangle in XY plane, rotation around Z
        Y, Z -> Rectangle in YZ plane, rotation around X
        X, Z -> Rectangle in XZ plane, rotation around Y
    '''

    # Isocenter-Referenced Shape
    half_length: float = length / 2
    half_width: float = width / 2

    # delete the conditions on axis
    # Define corners relative to the isocenter
    if axis_1 == "x" and axis_2 == "y":
        p1: np.ndarray = np.array([-half_length,  half_width, 0])
        p2: np.ndarray = np.array([ half_length,  half_width, 0])
        p3: np.ndarray = np.array([ half_length, -half_width, 0])
        p4: np.ndarray = np.array([-half_length, -half_width, 0])

    elif axis_1 == "y" and axis_2 == "z":
        p1: np.ndarray = np.array([0, -half_length,  half_width])
        p2: np.ndarray = np.array([0,  half_length,  half_width])
        p3: np.ndarray = np.array([0,  half_length, -half_width])
        p4: np.ndarray = np.array([0, -half_length, -half_width])

    elif axis_1 == "x" and axis_2 == "z":
        p1: np.ndarray = np.array([-half_length, 0,  half_width])
        p2: np.ndarray = np.array([ half_length, 0,  half_width])
        p3: np.ndarray = np.array([ half_length, 0, -half_width])
        p4: np.ndarray = np.array([-half_length, 0, -half_width])

    else:
        raise ValueError("Invalid axis combination. Use X/Y, Y/Z, or X/Z.")

    # Move points from isocenter-reference to robot/world coordinates
    p1 = p1 + isocenter
    p2 = p2 + isocenter
    p3 = p3 + isocenter
    p4 = p4 + isocenter

    # Store points in a list
    points: list = [p1, p2, p3, p4]
    
    return points






def rotate_points(points: list, angle: float=0.0):
    angle_radians = np.deg2rad(angle) # Convert from degrees to radians
    pass



def Rx(angle: float) -> np.ndarray[float]: 
    # type: (float) -> int
    return np.array([
        [1, 0            ,   0           ],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle),  np.cos(angle)],
        ])

def Ry(angle: float):
    return np.arry([
        [np.cos(angle)  ,   0 , np.sin(angle)],
        [0              ,   1 , 0          ],
        [-np.sin(angle) ,   0 , np.cos(angle)],
        ])

def Rz(angle: float):
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle),  np.cos(angle), 0],
        [0          ,  0          , 1],
        ])
    

# 1. Carry objects's frame/axis while it rotates
# 2. Leave behind the objects' frame and use that reference instead
