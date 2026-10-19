
# OLD PSEDUOCDOE BELOW
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
    coll_test_scan_data = []        # Tuple of both light and position data
    
    # Define path to move in (rectangle)
    coll_test_axes = ("y", "z") # Define active axes
    rectangle_points = paths.calculate_four_points_rectangle(est_isocenter, length, width,angle, coll_test_axes[0], coll_test_axes[1])
    rotated_points = paths.rotate_points(rectangle_points)
    path = paths.rectangle_path(est_isocenter, rotated_points, step)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, coll_test_light_data,  coll_test_position_data)
    # end_data_recording()

    # Process the Data
    # coll_test_scan_data = processData()


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
    gantry_test_scan_data = []        # Tuple of both light and position data
    
    # Define path to move in (rectangle)
    gantry_test_axes = ("y", "z") # Define active axes
    rectangle_points = paths.calculate_four_points_rectangle(est_isocenter, length, width,angle, gantry_test_axes[0], gantry_test_axes[1])
    path = paths.rectangle_path(est_isocenter, rectangle_points, step)

    # Move the robot and scan in the defined path
    # start_data_recording()
    move.execute_path(path, gantry_test_light_data,  gantry_test_position_data)
    # end_data_recording()

    # Process the Data
    # gantry_test_scan_data = processData()