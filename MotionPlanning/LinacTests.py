import numpy as np

import MotionPlanning.TestInitialization as TestInitialization
import MotionPlanning.MovementPaths as MovementPaths
import MotionPlanning.LightScanning as LightScanning

#TODO: Update Test Logic to Include Cases and Thresholds
def gravityTest(fr5=None):
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    #We also have the parameter gravityTesData ---> this would b the tuple version
    gravityTestData =  [((dx, dy, dz), lightIntensity)]
    gravityTestMovementData = gravityTestData[0]
    gravityTestLightData = gravityTestData[1]

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
    
    gravityTestData.start_recording(freq, Navg, 'initial_path')
    ipFound = LightScanning.initialPath(gravityTestData, path, fr5, threshold)
    gravityTestData.end_recording()

    TestInitialization.returnToHomePosition(fr5)

    #Scenarios
    if ipFound is False:
        step=4 
        gravityTestData.start_recording(freq, Navg, 'zeroPoint')
        zp_found = LightScanning.zeroPoint(length/int(step), fr5, gravityTestData, threshold)

        if zp_found is True:
            print("Found Laser During ZP Test") 
        else:
            print("No Points Found in ZP Test")
            print("Conducting Initial Path Again")
    
    #Change to While Loop Later --> Repeat Both Until Laser Found    

    
