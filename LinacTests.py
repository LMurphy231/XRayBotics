import time
import numpy as np
import numpy

import MovementPaths

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
