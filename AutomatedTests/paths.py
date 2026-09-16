import numpy as np

def rectangle_path(step, length, width):
    """
    rectangle_path
    """
    #Creating Moveset for Corner-Referenced Rectangle Path
    moves = []                      #Store Moveset
    sideOne = length/int(step)   #Number of Times to Increment for length side
    sideTwo = width/int(step)   #Number of Times to Increment for width side

    #Define Movement Vectors (x, y, z)
    pos_x = np.array([sideOne, 0, 0])
    #pos_y = np.array([0, sideOne, 0])
    pos_z = np.array([0, 0, sideTwo]) # Scan horizontal laser

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", -pos_x), ("-z", -pos_z)] #Tuple for Directions

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")

    # Debug
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {step} times")

    #Create Moves List
    for name, direction in directions:
        for _ in range(step):
            moves.append((name, direction))

    return moves


def rectangle_path_center_referenced(axes, step, length, width,):
    """
    rectanglePathUpdated
    axes = (x,y,z)
    Move in a rectangle (axis one at a time)
    """

    #Creating Moveset for Center-Referenced Rectangle Path
    moves = []          # Store Moveset
    active_axes = []    # Track which axes are being used
    
    #Define Movement Unit Vectors (x, y, z)  
    pos_x_uv = np.array([1, 0, 0])
    pos_y_uv = np.array([0, 1, 0])
    pos_z_uv = np.array([0, 0, 1])
    axis_uv = [pos_x_uv, pos_y_uv, pos_z_uv]
    
    side_length = length/int(step)      # Number of Times to Increment for length side
    side_width = width/int(step)       # Number of Times to Increment for width side
    
    # Scale the unit vector for the axes if it's enabled
    for i in range(len(axes)):
        if axes[i] == 0:
            axis_uv[i] *= 0 # Scale uv to 0
        elif count == 1:
            axis_uv *= side_width # Scale uv to first side length
        else:
            axis_uv *= side_length
            count += 1
    
    # Store which axes the rectangle will be moved in
    for i, axis in enumerate(axes):
        if axis != 0:
            active_axes.append(axis)
            
    # Scale the unit vector for the axes if it's enabled
    for i in range(active_axes):
        if active_axes == 0:
            axis_uv[i] *= 0
        else:
            active_axes *= side_length
    
    # Define final directions for the path
    move_x = ("+x", axis_uv[0])
    move_y = ("+y", axis_uv[1])
    move_z = ("+z", axis_uv[2])
    directions = [move_x, -move_x, move_y, -move_y, move_z, -move_z]
    
    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")

    # Debug
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {step} times")

    #Create Moves List
    for name, direction in directions:
        for _ in range(step):
            moves.append((name, direction))

    return moves