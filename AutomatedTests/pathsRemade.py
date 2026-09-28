import numpy as np
#import RobotCommunicator as com
#from LightSensor import SensorManager

# (x,y,z): tuple ---> immutable: can't change
# [x,y,z]: list ---> mutable: can change

def straight_path(p1: np.ndarray, p2: np.ndarray, step_length: int = 1.0, discrete: bool = False) -> list:
    """
    straight_path()
    Return a move list that stores the straight path
    Incremental or non-incremental
    Scan or no-scan afterwards
    ex:
        increment = 5
        p1 = (1,2,3)
        p2 = (4,5,6)
    """

    moves: list = []                # Store movements into a list
    displacement: np.ndarray        # Store the displacement vector
    movement: np.ndarray            # Store how much to move in each axis
    
    displacement = p2  - p1        # Find Magnitude displacement vector
    mag_displacement = np.linalg.norm(displacement)          # Find Magnitude displacement vector

    # Create moveset
    if discrete:
        # Find movement for each increment too
        n_steps: int = int(mag_displacement // step_length)  
        movement = displacement / n_steps
        #movement = displacement / step_length  
        for i in range(n_steps):         
            moves.append(movement)
        return moves  
    else:
        # Create one movement for entire path from p1 to p2 without increments
        movement = displacement
        moves.append(movement)
        return moves

def rectangle_path(isocenter: np.ndarray, points: list, step_length: int):
    """
    rectangle_path()
    Create the movement paths needed to travel around a rectangle.

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
    path_to_p1:     list = straight_path(isocenter, p1, step_length, False)   # Non-Incremental
    path_p1_to_p2:  list = straight_path(p1, p2, step_length, True)           # Incremental
    path_p2_to_p3:  list = straight_path(p2, p3, step_length, False)          # Non-Incremental
    path_p3_to_p4:  list = straight_path(p3, p4, step_length, True)           # Incremental

    # Store paths with scan information; True/False for Scanning
    rectangle_paths: list[tuple[list[np.ndarray], bool]]= [
        (path_to_p1, False),
        (path_p1_to_p2, True),
        (path_p2_to_p3, False),
        (path_p3_to_p4, True)
    ]

    return rectangle_paths

def calculate_four_points_trig(isocenter: np.ndarray, length: float, width: float, angle: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_trig
    Find the "4 corners" of the rectangle given L, W, angle, and active axes
    Center will be user-defined "isocenter" (origin)
    Angle is entered in degrees and converted to radians

    Valid axis combinations:
        X, Y -> Rectangle in XY plane, rotation around Z
        Y, Z -> Rectangle in YZ plane, rotation around X
        X, Z -> Rectangle in XZ plane, rotation around Y
    '''

    # Convert angle from degrees to radians for numpy
    angle_radians: float = convert_degrees_to_radians(angle)

    # Isocenter-Referenced Shape in rectangular fashion
    half_length: float = length / 2
    half_width: float = width / 2

    # Define corners relative to the isocenter; based on which 2 axes robot will be moving in
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

    # Calculate rotated points
    points: list = [p1, p2, p3, p4]
    rotated_points: list = []

    for point in points:

        # Extract coordinates
        x: float = point[0]
        y: float = point[1]
        z: float = point[2]

        # Find distance from isocenter using only the active axes
        if axis_1 == "x" and axis_2 == "y":
            radius: float = np.sqrt(x**2 + y**2)
            #original_angle: float = np.arctan2(y, x) # Angle to point AND User Angle Input

        elif axis_1 == "y" and axis_2 == "z":
            radius: float = np.sqrt(y**2 + z**2)
            #original_angle: float = np.arctan2(z, y)

        else:
            radius: float = np.sqrt(x**2 + z**2)
            #original_angle: float = np.arctan2(z, x)

        # Add requested rotation
        #new_angle: float = original_angle + angle_radians
        new_angle: float = angle_radians
        
        # Find new coordinates in the selected plane
        if axis_1 == "x" and axis_2 == "y":
            new_x: float = radius * np.cos(new_angle)
            new_y: float = radius * np.sin(new_angle)
            new_z: float = z

        elif axis_1 == "y" and axis_2 == "z":
            new_x: float = x
            new_y: float = radius * np.cos(new_angle)
            new_z: float = radius * np.sin(new_angle)

        elif axis_1 == "x" and axis_2 == "z":
            new_x: float = radius * np.cos(new_angle)
            new_y: float = y
            new_z: float = radius * np.sin(new_angle)

        # Create new 3D point
        new_point: np.ndarray = np.array([new_x, new_y, new_z])

        # Move from isocenter-reference to robot/world coordinates
        new_point = new_point + isocenter

        rotated_points.append(new_point)

    return rotated_points

def calculate_four_points_matrix(isocenter: np.ndarray, length: float, width: float,
                                 angle: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_matrix
    Find the "4 corners" of the rectangle given L, W, angle, and active axes
    Center will be user-defined "isocenter" (origin)
    Angle is entered in degrees and converted to radians

    Valid axis combinations:
        X, Y -> Rectangle in XY plane, rotation around Z
        Y, Z -> Rectangle in YZ plane, rotation around X
        X, Z -> Rectangle in XZ plane, rotation around Y
    '''

    # Convert angle from degrees to radians
    angle_radians: float = convert_degrees_to_radians(angle)

    # Isocenter-Referenced Shape
    half_length: float = length / 2
    half_width: float = width / 2

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

    # Rotation matrix
    if axis_1 == "x" and axis_2 == "y":
        # Rotation around Z-axis
        rotation_matrix: np.ndarray = np.array([
            [np.cos(angle_radians), -np.sin(angle_radians), 0],
            [np.sin(angle_radians),  np.cos(angle_radians), 0],
            [0,                      0,                     1]
        ])

    elif axis_1 == "y" and axis_2 == "z":
        # Rotation around X-axis
        rotation_matrix: np.ndarray = np.array([
            [1, 0,                      0],
            [0, np.cos(angle_radians), -np.sin(angle_radians)],
            [0, np.sin(angle_radians),  np.cos(angle_radians)]
        ])

    else:
        # Rotation around Y-axis
        rotation_matrix: np.ndarray = np.array([
            [ np.cos(angle_radians), 0, np.sin(angle_radians)],
            [0,                      1, 0],
            [-np.sin(angle_radians), 0, np.cos(angle_radians)]
        ])

    # Rotate points around the isocenter
    p1 = rotation_matrix @ p1
    p2 = rotation_matrix @ p2
    p3 = rotation_matrix @ p3
    p4 = rotation_matrix @ p4

    # Move points from isocenter-reference to robot/world coordinates
    p1 = p1 + isocenter
    p2 = p2 + isocenter
    p3 = p3 + isocenter
    p4 = p4 + isocenter

    # Store points in a list
    points: list = [p1, p2, p3, p4]

    return points

def convert_degrees_to_radians(angle: float):
    radians: float = angle * (np.pi / 180)
    return radians

def convert_radians_to_degrees(angle: float):
    degrees: float = angle * (180 / np.pi)
    return degrees

def calculate_four_points_matrix(isocenter: np.ndarray, length: float, width: float,
                                 angle: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_matrix
    Find the "4 corners" of the rectangle given L, W, angle, and active axes
    Center will be user-defined "isocenter" (origin)
    Angle is entered in degrees and converted to radians

    Valid axis combinations:
        X, Y -> Rectangle in XY plane, rotation around Z
        Y, Z -> Rectangle in YZ plane, rotation around X
        X, Z -> Rectangle in XZ plane, rotation around Y
    '''

    # Convert angle from degrees to radians
    angle_radians: float = convert_degrees_to_radians(angle)

    # Isocenter-Referenced Shape
    half_length: float = length / 2
    half_width: float = width / 2

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

    # 3 points: origin, p1, p2
    
    # Rotation matrix
    if axis_1 == "x" and axis_2 == "y":
        # Rotation around Z-axis
        rotation_matrix: np.ndarray = np.array([
            [np.cos(angle_radians), -np.sin(angle_radians), 0],
            [np.sin(angle_radians),  np.cos(angle_radians), 0],
            [0,                      0,                     1]
        ])
        
        
        rotate_z_matrix = lambda angle: np.array([
                [np.cos(angle), -np.sin(angle), 0],
                [np.sin(angle),  np.cos(angle), 0],
                [0,                      0,                     1]
            ])
            
        r = rotate_z_matrix(angle_radians) # Convert into radians first
        
    elif axis_1 == "y" and axis_2 == "z":
        # Rotation around X-axis
        
        rotation_matrix: np.ndarray = np.array([
            [1, 0,                      0],
            [0, np.cos(angle_radians), -np.sin(angle_radians)],
            [0, np.sin(angle_radians),  np.cos(angle_radians)]
        ])

    else:
        # Rotation around Y-axis
        rotation_matrix: np.ndarray = np.array([
            [ np.cos(angle_radians), 0, np.sin(angle_radians)],
            [0,                      1, 0],
            [-np.sin(angle_radians), 0, np.cos(angle_radians)]
        ])

    # Rotate points around the isocenter
    p1 = rotation_matrix @ p1
    p2 = rotation_matrix @ p2
    p3 = rotation_matrix @ p3
    p4 = rotation_matrix @ p4

    # Move points from isocenter-reference to robot/world coordinates
    p1 = p1 + isocenter
    p2 = p2 + isocenter
    p3 = p3 + isocenter
    p4 = p4 + isocenter

    # Store points in a list
    points: list = [p1, p2, p3, p4]

    return points

def calculate_four_points_(isocenter: np.ndarray, length: float, width: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_matrix
    Find the "4 corners" of the rectangle given L, W, angle, and active axes
    Center will be user-defined "isocenter" (origin)
    Angle is entered in degrees and converted to radians

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
    
    
    
    
    

def rotate_points():
    
Ry = lambda angle: np.array([
    
Rx = lambda angle: np.array([
    [1, 0            ,   0           ],
    [0, np.cos(angle), -np.sin(angle)],
    [0, np.sin(angle),  np.cos(angle)],
    ])
    
    
    
    
    pass

# 1. Carry objects's frame/axis while it rotates
# 2. Leave behind the objects' frame and use that reference instead
