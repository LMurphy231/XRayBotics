import numpy as np

import archive.MotionPlanning.TestInitialization as TestInitialization
import archive.MotionPlanning.Movement as Movement
import archive.MotionPlanning.MovementPaths as MovementPaths
import archive.MotionPlanning.LightScanning as LightScanning

import RobotCommunicator as com

#TODO: Update Test Logic to Include Cases and Thresholds
def gravityTest(fr5=None, freq=4500, Navg=4, threshold=0.75, 
                step=1, length=100, width=100):
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    #We also have the parameter gravityTesData ---> this would b the tuple version
    if fr5 is None:
        fr5 = com.RobotCom()

    fr5.home() # Start at home position
    #fr5._get_tool_position() # Show current position (home)
    print(f"{fr5._get_tool_position()}") #Debug output

    gravityTestData =  []
    path = MovementPaths.rectanglePath(step, length, width) # Define Input Path

    Movement.MoveRobot(fr5, path, testData, clamp) #Move in path







    #Conduct Movement in Input Path
    clamp = 0.5

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

    



#TODO ---> PSEUDOCODE for automated Gravity test
# Add more args
def gravity_test_automated(fr5=None, *args, x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100):

    # Define data to collect
        # grav_test_light_data[]
        # 

    # Return to home pos
    # Define path to move in (rectangle for now; optional: straight_paths)
        # path = rectangle(z, *args)
            # Defines max positions to prevent collisions


    # start_data_recording()
    # Call movement function to move in path: move(path)
        # while(moving "up +z" until max height)
            # Store light intensity data ---> append.light_data[]
            # Store positional data (movement vectors) ---> append.coordinates[(x,y,z)]
            # TODO [(dx,dy,dz), light_intensity] # Tuple array possibly
            
        # Process data ---> append to data lists ---> 

    # if not enough light data then move up to max_z
    return


# Add more args
#TODO ---> PSEUDOCODE
def collimator_test_automated(fr5=None, x, y, z, freq=4500, Navg=4, threshold=0.75, step=1, length=100, width=100):
    #here
    return