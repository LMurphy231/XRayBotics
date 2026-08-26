import numpy as np

import MotionPlanning.Movement as Movement
import MotionPlanning.LightScanning as LightScanning

#TODO: Remove/Modify/Fix initialPath() Function
#First path to guess where laser is located
def initialPath(testData, path, fr5, threshold):

    #Conduct Movement in Input Path
    lightData = []
    clamp = 0.5

    #Initial Move and Scan In Square Path: From Corner
    Movement.MoveRobot(fr5, path, testData, lightData, clamp)
    
    #Get Portion of Points Above Threshold per Move
    portions = []
    hits = []
    accuracyPercent = 0.1

    LightScanning.lightScanHits(lightData, threshold, portions, hits, accuracyPercent) #Conduct Light Scan

    #Update Found Status
    if len(hits) > 0:
        return True

    return False

#TODO: Remove/Modify/Fix/Refactor zeroPoint() Function
def zeroPoint(step, fr5, testData, threshold):

    max_z = 200 #Define Max Height (mm)
    z_moved = 0
    lightData = []
    hits = []
   
    #Detection Parameters
    clamp = 0.5
    accuracyPercent = 0.1

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
        if percent <= accuracyPercent:
            hits.append((z_moved, percent))  

            print(f"Hits: {hits}")
            print(f"[DETECTED LASER] at step {z_moved}, Portion = {percent} %")

            #End ZP Test: Found Laser
            testData.end_recording()

            return True

    testData.end_recording()

    return False
