import time
import numpy as np

def square_path(step, length):

    #Creating Moveset for Corner-Referenced Square Path
    moves = []                      #Store Moveset
    steps_full = length/int(step)   #Number of Times to Increment for Full Side

    #Define Movement Vectors (x and z)
    pos_x = np.array([0,steps_full, 0])
    pos_z = np.array([0, 0, steps_full])

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", -pos_x), ("-z", -pos_z)] #Tuple for Directions

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")

    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {step} times")

    #Create Moves List
    for name, direction in directions:
        for _ in range(step):
            moves.append((name, direction))

    return moves


