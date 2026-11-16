import time
import numpy as np

import archive.TestInitialization as TestInitialization
import Movement
import MovementPaths
import archive.LightScanning as LightScanning

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

def gravityTest(fr5=None, testData=None):
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    TestInitialization.initializeRobot()
    TestInitialization.returnToHomePosition(fr5)

    #Parameters
    freq = 4500                 # < 5000
    Navg = 4                    # < 5
    threshold = 0.75            #STC
    
    #Path Paramters
    step = 1 #STC
    length = 100 #mm
    width = 100
    path = MovementPaths.rectanglePath(step, length, width) #Input Path
    
    #Start Initial Scan
    
    testData.start_recording(freq, Navg, 'initial_path')
    ipFound = LightScanning.initialPath(testData, path, fr5, threshold)
    testData.end_recording()

    TestInitialization.returnToHomePosition(fr5)

    #Scenarios
    if ipFound is False:
        step=4 
        testData.start_recording(freq, Navg, 'zeroPoint')
        zp_found = LightScanning.zeroPoint(length/int(step), fr5, testData, threshold)

        if zp_found is True:
            print("Found Laser During ZP Test") 
        else:
            print("No Points Found in ZP Test")
            print("Conducting Initial Path Again")
    
    #Change to While Loop Later --> Repeat Both Until Laser Found    

    
