import numpy as np

def rectanglePath(step, length, width):
    """
    rectanglePath

    Inputs
    ------
     MORE
    """
    #Creating Moveset for Corner-Referenced Rectangle Path
    moves = []                      #Store Moveset
    sideOne = length/int(step)   #Number of Times to Increment for length side
    sideTwo = width/int(step)   #Number of Times to Increment for width side

    #Define Movement Vectors (x, y, z)
    pos_x = np.array([sideOne, 0, 0])
    #pos_y = np.array([0, sideOne, 0])
    pos_z = np.array([0, 0, sideTwo])

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


def rectanglePathUpdated(step, length, width, axes):
    """
    rectanglePathUpdated
    axes = (a,b)
    """

    if (len(axes) != 2):
        #print("Error! Must have exactly 2 axes to move in")
        raise ValueError("Error! Must have exactly 2 axes to move in")

    #Creating Moveset for Corner-Referenced Rectangle Path
    moves = []                      #Store Moveset
    sideOne = length/int(step)   #Number of Times to Increment for length side
    sideTwo = width/int(step)   #Number of Times to Increment for width side

    dimensions = (sideOne, sideTwo)

    #Define Movement Vectors (x, y, z)
    pos_x = np.array([sideOne, 0, 0])
    #pos_y = np.array([0, sideOne, 0])
    pos_z = np.array([0, 0, sideTwo])

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



def straightPath(step, length, direction):
    """
    straightPathX
    """   
    #Creating Moveset for Straight Path
    moves = []                      #Store Moveset
    path = length/int(step)   #Number of Times to Increment

    #Define Movement Vectors (x, y, z)
    pos_x = np.array([path, 0, 0])
    #pos_y = np.array([0, path, 0])
    pos_z = np.array([0, 0, path])

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
