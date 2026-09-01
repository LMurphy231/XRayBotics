import numpy as np

import MotionPlanning.LightScanning as LightScanning

try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC

#TODO: Update Logic on Moving Robot
# Generic Move Function
def MoveRobot(fr5, path, testData, lightData, clamp):
     """
     Move robot here #doc strings
     """
     for direction_name, move_vec in path: #Tuple Unpacking

        dx, dy, dz = move_vec
        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot
        testData.next_movement(dx, dy, dz)
        fr5._incriment_move(dx, dy, dz) #STC #TODO
        fr5._move_wait()
        data = testData.end_movement()


#main move function is above ^

#TODO: Complete Movement Actions and defined Movement states
class Movement:  # Movement Actions to be Performed    
    def __init__(self, arm):
        self.arm = arm

    def move(self, dx, dy, dz):
        self.arm.move(dx, dy, dz)

    def move_right(self, delta):
        self.arm.move(delta, 0, 0)
    
    def move_left(self, delta):
        self.arm.move(-delta, 0, 0)
    
    def move_down(self, delta):
        self.arm.move(0, 0, -delta)
    
    def move_up(self, delta):
        self.arm.move(0, 0, delta)

    def move_in(self, delta):
        self.arm.move(0, -delta, 0)

    def move_out(self, delta):
        self.arm.move(0, delta, 0)

#TODO: UPDATE FUNCTION TO PROPERLY TRACK HISTORY OF MOVEMENTS
def trackPosition(dx, dy, dz):
    #Track Position (Manual) 
    coord = np.array([0.0, 0.0, 0.0])
    coord += np.array([dx, dy, dz]) #For Manual Updates


