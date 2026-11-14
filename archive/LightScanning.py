import numpy as np

import Movement

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

#TODO #First path to guess where laser is located
def initialPath(testData, path, fr5, threshold):

    #Conduct Movement in Input Path
    lightData = []
    clamp = 0.5
    currentMax = 0

    #Initial Move and Scan In Square Path: From Corner
    Movement.MoveRobot(fr5, path, testData, lightData, clamp)
    
    #Get Portion of Points Above Threshold per Move
    portions = []
    hits = []
    acc_perc = 0.1

    for i, arr in enumerate(lightData): #Want to Track Index and Value 
        percent = len(arr[arr > threshold]) / len(arr)
        portions.append(percent) #Store Portions for Each Move

        if percent < acc_perc:
            hits.append((i, percent)) #Save Which Moves Had Light (Enough Values)

    print(f"Portions: {portions} --- Hits: {hits}")

    #Update Found Status
    if len(hits) > 0:
        return True

    return False

#TODO: REFACTORING
def zeroPoint(step, fr5, testData, threshold):

    max_z = 200 #Define Max Height (mm)
    z_moved = 0
    lightData = []
    hits = []
   
    #Detection Parameters
    clamp = 0.5
    acc_perc = 0.1

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    #Move Up in +z until found light or reach z threshold
    while z_moved < max_z:

        testData.next_movement(0, step, 0)
        fr5._incriment_move(0, step, 0)
        fr5._move_wait()
        data = testData.end_movement()

        z_moved += step

        _, intensities, *_ = testData.individualize(data)        #Get Light Data After Each Move
                                 #Clamp to 0                               

        #Check in Case Clamps All to 0; Normalize per Move
        norm_intensities = np.array(intensities) / max(np.max(intensities),1)
        norm_intensities[norm_intensities < clamp] = 0   
        
        lightData.append(norm_intensities) #Append Light Data; List of NumPy arrays

        #Check if Laser Found Early
        percent = len(norm_intensities[norm_intensities > threshold]) / len(norm_intensities)
        if percent <= acc_perc:
            hits.append((z_moved, percent))  

            print(f"Hits: {hits}")
            print(f"[DETECTED LASER] at step {z_moved}, Portion = {percent} %")

            #End ZP Test: Found Laser
            testData.end_recording()

            return True

    testData.end_recording()

    return False
