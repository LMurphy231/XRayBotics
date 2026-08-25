import time
import numpy as np

try:
    from api.farinoAPI.fairino.Robot import *
except:
    from Robot import RPC
    
from labquest import LabQuest 
try:
    #import GUI
    from GUI_remade import RobotCommunicator, LightSensor, TestData
except:
    pass

def MoveRobot(fr5, path, testData, lightData, clamp):
     for direction_name, move_vec in path: #Tuple Unpacking

        dx, dy, dz = move_vec
        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #Move Real Robot 
        testData.next_movement(dx, dy, dz)
        fr5._incriment_move(dx, dy, dz)
        fr5._move_wait()
        data = testData.end_movement()

        _, intensities, *_ = testData.individualize(data) #testData.result(testData.cur_move_id)        #Get Light Data After Each Move
                                    #Clamp to 0

        #Check in Case Clamps All to 0; Normalize per Move
        norm_intensities = np.array(intensities) / max(np.max(intensities),1)
        norm_intensities[norm_intensities < clamp] = 0   
            
        lightData.append(norm_intensities)                             #Append Light Data; List of NumPy arrays        










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

#Track Position (Manual) 
#coord = np.array([0.0, 0.0, 0.0])
#coord += np.array([dx, dy, dz]) #For Manual Updates TODO

