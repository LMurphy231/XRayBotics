import numpy as np
import RobotCommunicator as com

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


def rectangle_path_center_referenced(axes, step, length, width, angle):
    """
    rectanglePathUpdated
    axes = (x,y,z)
    Move in a rectangle (axis one at a time)
    """
    
    origin = [] # Most likely isocenter
    # Add length/width with angle (how to move) origin form points
    # x = rcos(theta)
    # y = 

    #Creating Moveset for Center-Referenced Rectangle Path
    moves = []          # Store Moveset
    active_axes = []    # Track which axes are being used
    
    #Define Movement Unit Vectors (x, y, z)  
    pos_x_uv = np.array([1, 0, 0])
    pos_y_uv = np.array([0, 1, 0])
    pos_z_uv = np.array([0, 0, 1])
    axis_uv = [pos_x_uv, pos_y_uv, pos_z_uv]
    
    length_side = length/int(step)      # Number of Times to Increment for length side
    half_length = 1/2 * length_side
    
    width_side = width/int(step)       # Number of Times to Increment for width side
    half_width = 1/2 * width_side
    
    # Scale the unit vector for the axes if it's enabled
    for i in range(len(axes)):
        if axes[i] == "0":
            axis_uv[i] *= 0 # Scale uv to 0
        elif count == 1:
            axis_uv *= side_width # Scale uv to first side length
        else:
            axis_uv *= side_length # Scale uv to second length
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
            
    # Centered reference scaling logic: given L X W dimensions and a1 and a2 for axis 1 and 2 respecitvely
    # 1. +a: 1/2 L
    # 2. +b: 1/2 W
    # 3. -a: L
    # 4. -b: L
    # 5. +a: L
    # 6. +b: 1/2 W
    
    move1 = axis_uv[active_axes[0]] * half_length
    move2 = axis_uv[active_axes[1]] * -1 * half_width
    move3 = axis_uv[active_axes[0]] * -1 * length_side
    move4 = axis_uv[active_axes[1]] * 
    
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

# Move point to point icnrementall and then scan AFTER each move
def point_to_point(fr5, dx1, dy1, dz1, dx2, dy2, dz2, distance):
    # Move Point A to Point B
    # Have step distance be constant
    for dist in range(0):
    
    source = (dx1, dy1, dz1)
    dest = (dx2, dy2, dz2) 
    com._position_move(fr5, )
    return

def straight_path():
    #Creating Moveset for Center-Referenced Rectangle Path
    moves = []          # Store Moveset
    # Track which axes are being used
    
    return

# r = sqrt(a^2 + b^2)
# floor function if non-integer
# Break down into functions

# Coordinates; debug for offset

def test_path():
    # Unit vectors
    # Give 2 axes you want only for now; any order for now
    arrs = [
        np.array([0,1,0]),
        np.array([0,0,1]),
    ]
    path = []
    current_cord = np.array([1,0,0])
    for i in range(2):
        current_cord = current_cord + arrs[1]*((-1)**i)
        for j in range(2):
            current_cord = current_cord + arrs[0]*(j*(-1)**(i))
            path.append(current_cord)
           
    for movement in path:
        print(movement)
    
    return

# Sam: move robot -> save that point
# how much he wants to move up/down, across, angles (collimator/gantry)