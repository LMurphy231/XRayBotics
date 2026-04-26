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

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", -pos_x), ("-z", -pos_z)] #Tuple for Directions

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {steps_full} times")

    #Create Moves List
    for name, direction in directions:
        for _ in range(steps_full):
            moves.append((name, direction))

    return moves

def initial_path(x,y,z, ip_data, path, fr5, threshold):

    found = False
    light_data = []

    #Initial Move and Scan In Square Path: From Corner
    for direction_name, move_vec in path: #Tuple Unpacking

        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot 
        ip_data.next_movement(dx, dy, dz)
        fr5._incriment_move(dx, dy, dz)
        fr5._move_wait()

        _, intensities, *_ = ip_data.result(ip_data.cur_move_id) #Get Light Data After Each Move
        norm_intensities = intensities / np.max(intensities)
        light_data.append(norm_intensities) #Append Light Data; List of NumPy arrays
        

    #Consildated Intensity Value into Single Center-Based Value // Ignore, 4/26/26
    #Check intensity values with threshold

    if norm_intensities > threshold:
        found = True


    ip_data.end_recording()

    #Check if there exists intensities that experience sharp jump -> found = True
        
    return found

def zero_point(step, fr5, x,y,z, zp_data, threshold):

    max_z = 200 #Define Max Height (mm)
    found = False
    

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    #Move Up in +z until found light or reach z threshold
    for step in range(max_z):

        zp_data.test_data.new_movement(0, 0, step)
        fr5.robot._incriment_move(0, 0, step)
        fr5.robot._move_wait()

        if intensity >= threshold:
            break

    zp_data.test_data.end_recording()

    return found

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    #Objects for Classes
    fr5 = RobotCommunicator()
    sensor = LightSensor() 

    #Parameters
    freq = 4500                 # < 5000
    Navg = 4                    # < 5
    threshold = 0.95            #STC
    
    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Path Paramters
    x, y, z = float(0), float(0), float(0)     #Track (x,y,z)
    step = 5 #STC
    length = 100 #mm
    path = square_path(step, length) #Input Path
    
    #Start Initial Scan
    ip_data = TestData(fr5, sensor) 
    ip_data.test_data.start_recording(freq, Navg, 'zero_point')
    ip_found = initial_path(x,y,z, ip_data, path, fr5, threshold)
     
    #Return to Home Position
    print(f"\n[Square Complete] Returning to Home Posiiton: {home_pos}")
    fr5.home()
    
    #Scenarios
    if ip_found is False:
        zp_data = TestData(fr5, sensor)
        zp_data.test_data.start_recording(freq, Navg, 'zero_point')
        zp_found = zero_point(step, fr5, x,y,z, zp_data, threshold)

        if zp_found is True:
            print("Found Laser During ZP Test")
    
    #Return to Home Position
        print(f"\n[ZP Complete] Return to Home Posiiton: {home_pos}")
        fr5.home()




if __name__ == "__main__": 
    grav_test()





    