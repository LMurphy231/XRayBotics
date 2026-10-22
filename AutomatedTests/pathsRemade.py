import numpy as np

#from XRBPlotter import Rx, Ry, Rz
#import RobotCommunicator as com
#from LightSensor import SensorManager

# (x,y,z): tuple ---> immutable: can't change
# [x,y,z]: list ---> mutable: can change

# ===================== MOTION PLANNING FUNCTIONS: POINTS, PATHS, ROTATIONS =====================

def straight_path_displacement(p1: np.ndarray, p2: np.ndarray) -> list:
    """
    straight_path_displacement()
    Return a move list that stores the straight path
    Returns displacement vector between 2 points, not absolute position
    ex:
        p1 = (1, 2, 3)
        p2 = (2, 4, 6)
        movement = (1, 2, 3)
    Hierarchy: lowest level function (point-level)
    """

    movement: list = []                # Store movements into a list
    displacement: np.ndarray        # Store the displacement vector
    movement: np.ndarray            # Store how much to move in each axis
    
    displacement = p2  - p1        # Find Magnitude displacement vector
  
    # Create moveset:  one movement for entire path from p1 to p2 without increments
    movement.append(displacement)
    return movement

def straight_path_absolute(end_pos: np.ndarray):
    """
    Return the absolute destination position for a straight path.
    
    ASSSUMES: start_pos
    """

    abs_movement_path: list = []
    abs_movement_path.append(end_pos.copy())

    return abs_movement_path

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
    path_to_p1:     list = straight_path_absolute(p1)       # Non-Incremental
    path_p1_to_p2:  list = straight_path_displacement(p1, p2)   # Incremental
    path_p2_to_p3:  list = straight_path_absolute(p3)       # Non-Incremental
    path_p3_to_p4:  list = straight_path_displacement(p3, p4)   # Incremental

    # Store paths with scan information; True/False for Scanning
    rectangle_paths: list[tuple[list[np.ndarray], bool, np.ndarray]]= [
        (path_to_p1, False, p1)
        (path_p1_to_p2, True, p1),
        (path_p2_to_p3, False, p2),
        (path_p3_to_p4, True, p3)
    ]

    return rectangle_paths

def basis_plane_calculate_four_points(isocenter: np.ndarray, length: float, width: float):
    '''
    basis_plane(isocenter: np.ndarray, length: float, width: float)
        Find the "4 corners" of the rectangle given  isocenter (origin), length (L), width (W)
        
        Center will be user-defined "isocenter" (origin)
        
        If isoceneter = (0,0,0) -> pointsa are both abs pos and displacement
        If isoceneter != (0,0,0) -> points are only abs pos
        
        ASSUMES: Rectangle in XY plane (basis)
    '''
    
    # Isocenter-Referenced Shape
    half_length: float = length / 2
    half_width: float = width / 2
    
    p1: np.ndarray = np.array([-half_length,  half_width, 0]) # Top-left corner     (-x, +y, 0)
    p2: np.ndarray = np.array([ half_length,  half_width, 0]) # Top-right corner    (+x, +y, 0)
    p3: np.ndarray = np.array([ half_length, -half_width, 0]) # Bottom-right corner (+x, -y, 0)
    p4: np.ndarray = np.array([-half_length, -half_width, 0]) # Bottom-left corner  (-x, -y, 0)
    
    # Move points from isocenter-reference to robot/world coordinates
    p1 = p1 + isocenter
    p2 = p2 + isocenter
    p3 = p3 + isocenter
    p4 = p4 + isocenter

    points: list = [p1, p2, p3, p4] # Store points in a list
    
    return points

def rotate_basis_plane_points(isocenter: np.ndarray, points: list, rotation_matrix: np.ndarray):
    '''
    rotate_basis_plane_points(points: list, rotation_matrix: np.ndarray):
        Rotate list of points of basis plane using rotation matrix
    '''

    rotated_point: np.ndarray # Extract the rotated point from the rotation matrix
    rotated_points: list = [] # Store rotated points
    
    for point in points:
        relative_point: np.ndarray = point - isocenter
        rotated_point = rotate_point_with_matrix(relative_point, rotation_matrix)    # Rotate the points
        rotated_point = rotated_point + isocenter
        rotated_points.append(rotated_point)                                # Add to list of newly rotated points 

    return rotated_points

def rotate_point_with_matrix(point: np.ndarray, rotation_matrix: np.ndarray):
    '''
    rotate_point_with_matrix(point: np.ndarray, rotation_matrix: np.ndarray):
        Rotate a single point using rotation matrix
        Hierarchy: lowest level function (point-level)
    '''
    return rotation_matrix @ point
   
def rotation_matricies(matrix1: np.ndarray, rotation_matricies: list[np.ndarray]):
    '''
    rotation_matricies(matrix1: np.ndarray, rotation_matricies: list[np.ndarray]):
        Multiply multiple rotation matrices (list) together
    '''
    
    new_matrix: np.ndarray = matrix1.copy() # New matrix created by multiplying the rotation matrices together
    
    for matrix in rotation_matricies:
        new_matrix = np.matmul(matrix1, matrix)
    return new_matrix
   
 # =================================================================================  

   
# ===================== ROTATION MATRICES FOR EACH LINAC TEST ==========================

def gravity_test_rotation_matrix(grav_angle: float):
    return rotation_matricies(Ry(np.deg2rad(-90)), ) #TODO:

def collimator_test_rotation_matrix(col_angle, gan_angle):
    # start in YZ
    # rotate about y
    return rotation_matricies(Ry(np.deg2rad(-90)), )#TODO:

def gantry_test_rotation_matrix(gantry_angle, gan_angle):
    # start in YZ
    # rotate about y
    return rotation_matricies(Rx(np.deg2rad(-90)), )#TODO:

# =================================================================================  

# ===================== ROTATION MATRICES FOR EACH AXIS ==========================
def Rx(angle: float): 
    # type: (float) -> int
    return np.array([
        [1, 0            ,   0           ],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle),  np.cos(angle)],
        ])

def Ry(angle: float):
    return np.array([
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

# =================================================================================  


# ===================== HELPER FUNCTIONS ==========================================
def get_rotation_matrix(axis: str, angle: float, offset: float):
    '''
    get_rotation_matrix_(points: list, angle: float)
        Create a rotation matrix for a given angle and apply it to a list of points
    # HELPER FUNCTION
    '''
    angle_radians = np.deg2rad(angle + offset) # Convert from degrees to radians; ASSUMES + = CCW
        
    rotation_matrix: np.ndarray

    # Determine which axis to rotate about
    if axis == "x":
        rotation_matrix = Rx(angle_radians) # Rotate about x-axis
    elif axis == "y":
        rotation_matrix = Ry(angle_radians) # Rotate about y-axis
    elif axis == "z":
        rotation_matrix = Rz(angle_radians) # Rotate about z-axis
    else:
        raise ValueError("Invalid rotation axes.")

    return rotation_matrix

# =================================================================================  




# 1. Carry objects's frame/axis while it rotates
# 2. Leave behind the objects' frame and use that reference instead



# OLD FUNCTIONS BELOW; DONT DELETE; MAY BE USEFUL LATER

def calculate_four_points_rectangle(isocenter: np.ndarray, length: float, width: float, axis_1: str, axis_2: str):
    '''
    calculate_four_points_rectangle
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
        p1: np.ndarray = np.array([-half_length,  half_width, 0]) # Top-left corner
        p2: np.ndarray = np.array([ half_length,  half_width, 0]) # Top-right corner
        p3: np.ndarray = np.array([ half_length, -half_width, 0]) # Bottom-right corner
        p4: np.ndarray = np.array([-half_length, -half_width, 0]) # Bottom-left corner

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

def rotate_points(points: list, angle: float, axis_1: str, axis_2: str):
    '''
    Rotate list of points
    Plane XY ---> Rotate about Z ---> Rz
    Plane XZ ---> Rotate about Y ---> Ry
    Plane YZ ---> Rotate about X ---> Rx
    
    Angle given in degrees ---> must convert to radians
    
    def rotate_points(points: list, angle: float, test: str):
    
    multiple rotations: input is 1 rotation matrix, list of points
    fcn (matrix, points: list)
    '''
    
    angle_radians = np.deg2rad(angle) # Convert from degrees to radians; ASSUMES + = CCW
    
    # Determine which axis to rotate about
    if axis_1 == "x" and axis_2 == "y":
        rotation_matrix: np.ndarray = Rz(angle_radians) # Rotate about z-axis
    elif axis_1 == "x" and axis_2 == "z":
        rotation_matrix: np.ndarray = Ry(angle_radians) # Rotate about y-axis
    elif axis_1 == "y" and axis_2 == "z":
        rotation_matrix: np.ndarray = Rx(angle_radians) # Rotate about x-axis
    else:
        raise ValueError("Invalid plane axes.")

    rotated_points: list = []

    for point in points:
        rotated_point: np.ndarray = rotation_matrix @ point # Rotate the points
        rotated_points.append(rotated_point)

    return rotated_points

def rotation_matrix(points: list, angle: float):
    '''
    rotation_matrix_point(points: list, angle: float)
        Create a rotation matrix for a given angle and apply it to a list of points
    '''
    
    angle_radians = np.deg2rad(angle) # Convert from degrees to radians; ASSUMES + = CCW
    
    rotation_matrix = Ry(np.deg2rad(angle))
    return rotate_points_basis_plane(points, rotation_matrix)