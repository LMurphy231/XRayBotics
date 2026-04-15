from enum import Enum, auto
import random
#import numpy as np

#States for different linac tests (QA)
# Move -> Search -> Scan; All Seperate Functions IDeally

class LinacQATest(Enum):
    GRAVITY = auto()
    GANTRY = auto()
    COLLIMATOR = auto()
    LIGHT_FIELD = auto()
    IDLE = auto()

class ArmSim:
    def __init__(self):
        #self.init_pos = [0,0,0] #STC: Find initial Pose
        #print(f"Initial Position: {self.init_pos}")

        self.position = [0, 0, 0]
        #print(f"Current Position: {self.position}")

    def move(self, dx, dy, dz):
        #x, y, z = self.coordinate
        #self.coordinate = [x + dx, y + dy, z + dz]

        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz
        #print(f"New Position: {self.position}")
    
    def move_complete(self):
        return True

class MovementSim:  # Movement Actions to be Performed    
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


    def light_scan(self, arm_pos, light_pos):
        x,y,z = arm_pos
        lx,ly,lz = light_pos
        dx = x - lx
        dy = y - ly
        dz = z - lz

        #STC: Call real function to get light data
        sim_data = 1.0 / (1.0 + dx*dx + dy*dy + 0.5*dz*dz)
        noise = random.uniform(-0.05, 0.05)

        return max(0.0, sim_data + noise)
 
class LightSim:
    def light_scan(self, arm_pos, light_pos):
        x,y,z = arm_pos
        lx,ly,lz = light_pos
        dx = x - lx
        dy = y - ly
        dz = z - lz

        #STC: Call real function to get light data
        sim_data = 1.0 / (1.0 + dx*dx + dy*dy + 0.5*dz*dz)
        noise = random.uniform(-0.05, 0.05)

        return max(0.0, sim_data + noise)

class GravSim:
    class STATE:
        INIT = 0
        SCAN = 1
        MOVE = 2
        COMPLETE = 3

    def __init__(self, arm, movement, sensor, light_pos):
        self.arm = arm
        self.movement = movement
        self.sensor = sensor
        self.light_pos = light_pos
        self.state = self.STATE.INIT

        self.final_light = 0
        self.final_pos = self.arm.position.copy()

        self.delta = 1 #STC
        self.scan_deltas = [
            (0, 0, 0),
            (self.delta, 0, 0),
            (-self.delta, 0, 0),
            (0, 0, self.delta),
            (0, 0, -self.delta),
        ]

    def run(self):
        if self.state == self.STATE.INIT:
            print("Starting Gravity Test...")
            self.arm.position = [0,0,0] #STC
            print(f"Returning to Initial Pose: {self.arm.position}")
            self.state = self.STATE.SCAN

        elif self.state == self.STATE.SCAN:
            print("Scanning Light for Laser...")
            curr_pos = self.arm.position
            curr_light = self.sensor.light_scan(curr_pos, self.light_pos)
            print(f"Current Position: {curr_pos}, Current Light Intensity: {curr_light}")

            #test_iso = [5,5,5] #STC (mm)
            test_iso = [random.randint(1, 50), random.randint(1, 50), random.randint(1, 50)]
            print(f"Moving to Found Isocenter: {test_iso}")

            #Move To Isocenter (mm) From Initial Pose
            idx = test_iso[0] - curr_pos[0]
            idy = test_iso[1] - curr_pos[1]
            idz = test_iso[2] - curr_pos[2]

            iso_move = idx, idy, idz
            print(f"Vector (Isocenter - Initial): {iso_move}")
            self.movement.move(*iso_move)
            curr_pos = test_iso
            print(f"Current Position (curr_pos): {curr_pos}")

            #Move in Square
            #Square Dimensions (mm) Use Even Dimensions for Now
            x = 5 #STC
            y = 10 #STC
            z = 0 #STC
          
            #Movement Deltas STC
            delta_x = 1
            delta_y = 1
            #delta_z = 1

            #1. Move in +x
            for i in range(x):
                next_move = delta_x, 0, 0 #Define Next Movement
                print(f"Next Move Distances: {next_move}") 

                self.movement.move(*next_move) #Call Move

                print(f"Current Position (arm.position): {self.arm.position}")

                dx = self.arm.position[0] - curr_pos[0]  #Find Difference in Moved Distance
                print(f"dx: {dx}")

                vect = dx, 0, 0 #Make Distance Vector
                print(f"Vector Movement: {vect}") #Show Distance Vector
                curr_pos = [curr_pos[0]+dx, curr_pos[1], curr_pos[2]]

                curr_light = self.sensor.light_scan(curr_pos, self.light_pos)
                print(f"Current Light Value: {curr_light}")

                if curr_light > self.final_light:
                    self.final_light = curr_light
                    self.light_pos = curr_pos.copy()
                    print(f"New Light Value: {self.final_light}")
                    print(f"New Light Position: {self.light_pos}")

            #2. Move in +y


            self.final_pos = iso_move
            self.state = self.STATE.COMPLETE
             
        elif self.state == self.STATE.COMPLETE:
            print("GRAVITY Test Complete")
            print(f"Final Position (At Isocenter): {self.final_pos}")
            #print(f"Best Light: {self.final_light}")
            return True
         
def grav_sim():
    print("----- Gravity Simulation -----")
    arm = ArmSim()
    movement = MovementSim(arm)
    light_sim = LightSim()

    light_pos = [3, 3, 0] #STC: Simulation

    sim = GravSim(arm, movement, light_sim, light_pos)

    done = False
    steps = 0

    while not done and steps < 50:
        done = sim.run()
        steps += 1

    #return sim.

if __name__ == "__main__": 
    fsm = grav_sim()
    #print("Gravity FSM Results: ", fsm)
    #print("Gravity Test Complete")

# Inputs: (curr_pos, movement vector, length of path deltas)
# Outputs: fcn for singal processing -> (final_pos, center_loc, vect_cent, errors, light_intensity)

#name:type --> var:int=5
