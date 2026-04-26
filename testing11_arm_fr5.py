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

    light_data = []
    clamp = 0.5
    curr_max = 0

    #Initial Move and Scan In Square Path: From Corner
    for direction_name, move_vec in path: #Tuple Unpacking

        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot 
        ip_data.next_movement(dx, dy, dz)
        fr5._incriment_move(dx, dy, dz)
        fr5._move_wait()

        _, intensities, *_ = ip_data.result(ip_data.cur_move_id)        #Get Light Data After Each Move
        intensities[intensities < clamp] = 0                            #Clamp to 0

        #Check in Case Clamps All to 0; Normalize per Move
        curr_max = np.max(intensities)
        if curr_max == 0:
            norm_intensities = np.array(intensities)
        else:
            norm_intensities = np.array(intensities) / curr_max
            
        light_data.append(norm_intensities)                             #Append Light Data; List of NumPy arrays        

    ip_data.end_recording()
    
    #Get Portion of Points Above Threshold per Move
    portions = []
    hits = []
    acc_perc = 0.1

    for i, arr in enumerate(light_data): #Want to Track Index and Value 
        percent = np.sum(arr > threshold) / len(arr)
        portions.append(percent) #Store Portions for Each Move

        if percent >= acc_perc:
            hits.append((i, percent)) #Save Which Moves Had Light (Enough Values)

    print(f"Portions: {portions} --- Hits: {hits}")

    #Update Found Status
    if len(hits) > 0:
        return True

    
    return False

def zero_point(step, fr5, zp_data, threshold):

    max_z = 200 #Define Max Height (mm)
    z_moved = 0
    light_data = []
    hits = []
   
    #Detection Parameters
    clamp = 0.5
    acc_perc = 0.1

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    #Move Up in +z until found light or reach z threshold
    while z_moved < max_z:

        zp_data.new_movement(0, 0, step)
        fr5._incriment_move(0, 0, step)
        fr5._move_wait()

        z_moved += step

        _, intensities, *_ = zp_data.result(zp_data.cur_move_id)        #Get Light Data After Each Move
        intensities[intensities < clamp] = 0                            #Clamp to 0                               

        #Check in Case Clamps All to 0; Normalize per Move
        curr_max = np.max(intensities)
        if curr_max == 0:
            norm_intensities = np.array(intensities)
        else:
            norm_intensities = np.array(intensities) / curr_max
        
        light_data.append(norm_intensities) #Append Light Data; List of NumPy arrays

        #Check if Laser Found Early
        percent = np.sum(norm_intensities > threshold) / len(norm_intensities)
        if percent >= acc_perc:
            hits.append((z_moved, percent))  

            print(f"Hits: {hits}")
            print(f"[DETECTED LASER] at step {z_moved}, Portion = {percent} %")

            #End ZP Test: Found Laser
            zp_data.end_recording()

            return True

    zp_data.end_recording()

    return False

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    #Objects for Classes
    fr5 = RobotCommunicator()
    sensor = LightSensor() 

    #Parameters
    freq = 4500                 # < 5000
    Navg = 4                    # < 5
    threshold = 0.75            #STC
    
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
    ip_data.start_recording(freq, Navg, 'zero_point')
    ip_found = initial_path(x,y,z, ip_data, path, fr5, threshold)
     
    #Return to Home Position
    print(f"\n[Square Complete] Returning to Home Posiiton: {home_pos}")
    fr5.home()
    
    #Scenarios
    if ip_found is False: 
        zp_data = TestData(fr5, sensor)
        zp_data.start_recording(freq, Navg, 'zero_point')
        zp_found = zero_point(step, fr5, zp_data, threshold)

        if zp_found is True:
            print("Found Laser During ZP Test") 
        else:
            print("No Points Found in ZP Test")
            print("Conducting Initial Path Again")
    
    #Change to While Loop Later --> Repeat Both Until Laser Found    

    #Return to Home Position
        print(f"\n[ZP Complete] Return to Home Posiiton: {home_pos}")
        fr5.home()




if __name__ == "__main__": 
    grav_test()





    