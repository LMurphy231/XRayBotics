import time
import numpy as np
import numpy
try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC
    
from labquest import LabQuest 
try:
    import GUI
    #from GUI import RobotCommunicator, LightSensor, TestData
except:
    pass
#Update: 4/26/26, 2:10pm

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

def initial_path(test_data, path, fr5, threshold):

    #Conduct Movement in Input Path
    light_data = []
    clamp = 0.5
    curr_max = 0

    #Initial Move and Scan In Square Path: From Corner
    for direction_name, move_vec in path: #Tuple Unpacking

        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot 
        test_data.next_movement(dx, dy, dz)
        fr5._incriment_move(dx, dy, dz)
        fr5._move_wait()
        data = test_data.end_movement()

        _, intensities, *_ = test_data.individualize(data) #test_data.result(test_data.cur_move_id)        #Get Light Data After Each Move
                                 #Clamp to 0

        #Check in Case Clamps All to 0; Normalize per Move
        norm_intensities = np.array(intensities) / max(np.max(intensities),1)
        norm_intensities[norm_intensities < clamp] = 0   
            
        light_data.append(norm_intensities)                             #Append Light Data; List of NumPy arrays        

    test_data.end_recording()
    
    #Get Portion of Points Above Threshold per Move
    portions = []
    hits = []
    acc_perc = 0.1

    for i, arr in enumerate(light_data): #Want to Track Index and Value 
        percent = len(arr[arr > threshold]) / len(arr)
        portions.append(percent) #Store Portions for Each Move

        if percent < acc_perc:
            hits.append((i, percent)) #Save Which Moves Had Light (Enough Values)

    print(f"Portions: {portions} --- Hits: {hits}")

    #Update Found Status
    if len(hits) > 0:
        return True

    return False

def zero_point(step, fr5, test_data, threshold):

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

        test_data.next_movement(0, step, 0)
        fr5._incriment_move(0, step, 0)
        fr5._move_wait()
        data = test_data.end_movement()

        z_moved += step

        _, intensities, *_ = test_data.individualize(data)        #Get Light Data After Each Move
                                 #Clamp to 0                               

        #Check in Case Clamps All to 0; Normalize per Move
        norm_intensities = np.array(intensities) / max(np.max(intensities),1)
        norm_intensities[norm_intensities < clamp] = 0   
        
        light_data.append(norm_intensities) #Append Light Data; List of NumPy arrays

        #Check if Laser Found Early
        percent = len(norm_intensities[norm_intensities > threshold]) / len(norm_intensities)
        if percent <= acc_perc:
            hits.append((z_moved, percent))  

            print(f"Hits: {hits}")
            print(f"[DETECTED LASER] at step {z_moved}, Portion = {percent} %")

            #End ZP Test: Found Laser
            test_data.end_recording()

            return True

    test_data.end_recording()

    return False

def grav_test(fr5=None, test_data=None):
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    #Objects for Classes
    if fr5 is None:
        fr5 = GUI.RobotCommunicator()
    if test_data is None:
        sensor = GUI.LightSensor() 
        test_data = GUI.TestData(fr5, sensor) 

    #Parameters
    freq = 4500                 # < 5000
    Navg = 4                    # < 5
    threshold = 0.75            #STC
    
    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Track Position (Manual)
    #coord = np.array([0.0, 0.0, 0.0])
    #coord += np.array([dx, dy, dz]) #For Manual Updates
    
    #Path Paramters
    step = 1 #STC
    length = 100 #mm
    path = square_path(step, length) #Input Path
    
    #Start Initial Scan
    
    test_data.start_recording(freq, Navg, 'initial_path')
    ip_found = initial_path(test_data, path, fr5, threshold)
     
    #Return to Home Position
    print(f"\n[Square Complete] Returning to Home Posiiton: {home_pos}")
    fr5.home()
    
    #Scenarios
    if ip_found is False:
        step=4 
        test_data.start_recording(freq, Navg, 'zero_point')
        zp_found = zero_point(length/int(step), fr5, test_data, threshold)

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





    