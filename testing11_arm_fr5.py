import time
import numpy as np
import numpy
from api.farinoAPI.fairino.Robot import *
from tkinter import *
from GUI import RobotCommunicator, LightSensor, TestData

#Check here: 4/26/26

class dummy_sensor:
    def dummy_light(self):
        return round(np.random.random(),3)

def square_move(step, length):

    half = length/2 #Half Side Movement
    moves = [] #Store Moveset

    steps_full = int(length/step) #Number of Times to Increment for Full Side
    steps_half = int(half/step)

    #Define Movement Vectors (x and z)
    pos_x = np.array([step, 0, 0])
    neg_x = np.array([-step, 0, 0])
    pos_z = np.array([0, 0, step])
    neg_z = np.array([0, 0, -step])

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", neg_x), ("-z", neg_z)]

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {steps_full} times")

    for name, direction in directions:
        for _ in range(steps_full):
            moves.append((name, direction))

    return moves

def move_square(step, length, plane=numpy.array([1, 0, 1]), center=False):
    if center:
        raise NotImplementedError
    plane_count = plane[plane != 0]
    if sum() != 2:
        raise ValueError(f'Plane set incorrectly {plane} ')
    
def initial_square(x,y,z,sensor,data, square_path, fr5, home_pos):

    points = 0 #Track Number of Light Points for Initial Scan
    move_data = []
    light_data = []

    #Initial Move and Scan In Square Path
    for direction_name, move_vec in square_path:
        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #STC: Move Real Robot 
        #fr5._incriment_move(dx, dy, dz)

        ##Update (xz Plane)
        x += float(dx)
        z += float(dz)

        #STC: Read Real Sensor
        intensity = sensor.dummy_light()
        #intensity = sensor.get()
        threshold = 0.95 #STC

        #Consildated Intensity Value into Single Center-Based Value

        if intensity > threshold: #STC
            points+= 1

        print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")

        data.append((x, z, intensity)) #Track (step,x,z,intensity)

        move_data.append((x, z))
        light_data.append(intensity)

    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()

    print(f"\nMove Data Collected: {move_data}")
    print(f"\nLight Data Collected: {light_data}")
    print(f"\nData Collected: {data}")

    print(f"\nNumber of Light Points Found Past Threshold (Initial Scan): {points}")

    return points


def zero_point(step,sensor,fr5, x,y,z):
    points = 0
    max_z = 50 #cm
    threshold = 0.95
    light_data = []
    hits = []
    inc= step
    it = 0

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    #Move Up in +z until found light or reach z threshold
    for i in range(max_z):
        z += float(inc) #Update z position

        #fr5._increment_move(0,0,step) #Move
        intensity = sensor.dummy_light() #STC
        #intensity = sensor.get()
        light_data.append(intensity)

        if intensity >= threshold:
            points += 1
            hits.append((z, intensity))
            print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")
            print("\nBreaking")
            break

        it += 1

    if points == 0: #Move Down now
        pass

    print(f"\nTotal Num of Iterations: {it}")
    print(f"\nNumber of Light Points Found (Zero-Test): {points}")
    print(f"\nHits Collected: {hits}")
    
    return points

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    fr5 = RobotCommunicator()
    sensor = dummy_sensor() #STC
    #sensor = LightSensor() #STC
    
    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Path Paramters
    step = 5 #STC
    length = 10 #mm
    square_path = square_move(step, length)
    x, y, z = float(0), float(0), float(0)     #Track (x,z)
    data = []                                  #(x,z,intensity)

    #Start Initial Scan
    points = initial_square(x,y,z,sensor,data, square_path, fr5, home_pos)
    
    #Scenarios
    if points == 0:
        points = zero_point(step, sensor, fr5, x,y,z)
    

    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()






if __name__ == "__main__": 
    grav_test()





    