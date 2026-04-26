import time
import numpy as np
import numpy
from api.farinoAPI.fairino.Robot import *
from labquest import LabQuest 

from GUI import RobotCommunicator, LightSensor, TestData

#Update: 4/26/26

def square_path(step, length):

    moves = [] #Store Moveset
    steps_full = int(length/step) #Number of Times to Increment for Full Side

    #Define Movement Vectors (x and z)
    pos_x = np.array([step, 0, 0])
    pos_z = np.array([0, 0, step])

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", -pos_x), ("-z", -pos_z)]

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {steps_full} times")

    for name, direction in directions:
        for _ in range(steps_full):
            moves.append((name, direction))

    return moves


def initial_square(x,y,z,sensor, data, square_path, fr5, home_pos, freq, Navg):

    found = False
    points = 0 #Track Number of Valid Light Points for Initial Scan
    move_data = []
    light_data = []
 
    data.test_data.start_recording(freq, Navg, 'grav_test')

    #Initial Move and Scan In Square Path
    for direction_name, move_vec in square_path:

        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot 
        data.test_data.new_movement(dx, dy, dz)
        fr5.robot._incriment_move(dx, dy, dz)
        fr5.robot._move_wait()

        #Update (xz Plane)
        x += float(dx)
        z += float(dz)

        #Consildated Intensity Value into Single Center-Based Value

        if intensity > threshold: #STC
            pass

    data.test_data.end_recording()

    #Check if all intensities are below threshold

    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()

    print(f"\nMove Data Collected: {move_data}")
    print(f"\nLight Data Collected: {light_data}")
    print(f"\nData Collected: {data}")

    print(f"\nNumber of Light Points Found Past Threshold (Initial Scan): {points}")

    return found



def zero_point(step,sensor, fr5, x,y,z, zp_data, freq, Navg):
    points = 0
    max_z = 50 #cm
    threshold = 0.95
    hits = []
    inc= step
    it = 0

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    zp_data.test_data.start_recording(freq, Navg, 'zero_point')

    #Move Up in +z until found light or reach z threshold
    for i in range(max_z):

        z += float(inc) #Update z position

        zp_data.test_data.new_movement(0, 0, step)
        fr5.robot._incriment_move(0, 0, step)
        fr5.robot._move_wait()

        if intensity >= threshold:
            points += 1
            print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")
            print("\nBreaking")
            break

        it += 1

    zp_data.test_data.end_recording()

    print(f"\nTotal Num of Iterations: {it}")
    print(f"\nNumber of Light Points Found (Zero-Test): {points}")
    print(f"\nHits Collected: {hits}")
    
    return points

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    fr5 = RobotCommunicator()
    sensor = LightSensor() 
    data = TestData(fr5, sensor) 
    freq = 4500     # < 5000
    Navg = 4        # < 5
    

    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Path Paramters
    x, y, z = float(0), float(0), float(0)     #Track (x,z)
    step = 5 #STC
    length = 100 #mm
    path = square_path(step, length)
    

    #Start Initial Scan
    is_found = initial_square(x,y,z,sensor,data, path, fr5, home_pos, freq, Navg)
    
    #Scenarios
    if is_found is False:
        zp_data = TestData(fr5, sensor)
        points = zero_point(step, sensor, fr5, x,y,z, zp_data, freq, Navg)
    
    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()


if __name__ == "__main__": 
    grav_test()





    