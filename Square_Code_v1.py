#Test Code v1
import numpy as np
from api.farinoAPI.fairino.Robot import *

class RobotCommunicator():
    def __init__(self):
        self.com = RPC()
        
        self.HOME = [0, -125.517, 124.552, 3.64, 85.43, 95.241]
        #self.home()


        # Save Stop motion function in case of error. 
        # Will update to the current movement type's stop
        self.motion_stop = None

    def _incriment_move(self, dx, dy, dz, ref=4, vel=20.0, acc=100.0, *vars):
        '''
        Move Arm with incrimental movements. 

        ref: Movement reference
         0 - joint point movement
         2 - base coordinate system point movement
         4 - tool coordinate system point movement
         8 - workpiece coordinate system point movement

        vel: Velocity - default: 20.0
        
        acc: Acceleration - default: 100.0
        '''
        self.motion_stop = self.com.StopMotion
        print(f'Moving by {(dx, dy, dz)}')
        current_pose = numpy.array(self.com.GetActualTCPPose(0)[1])
        new_pose = current_pose + numpy.array([dx, dy, dz, 0, 0, 0])
        print(new_pose)
        joint_pos = self._invk(*new_pose, type=0)
        print(joint_pos)


        self._joint_move(joint_pos, tool=0)

        self.motion_stop = None
        return False
    
    def _position_move(self, x, y, z, ref=4, vel=20.0, acc=100.0, *vars):
        '''
        '''
        self.motion_stop = self.com.StopMotion
        ierr = self.com.MoveL([], vel, acc)
        if ierr:
            self.motion_stop()
            print(ierr)
            return True

        self.motion_stop = None
        return False
    
    def home(self):
        self._joint_move(self.HOME)

    def _joint_move(self, joint_pos, tool=0, user=0, desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0], vel = 20.0, acc = 0.0, 
                    ovl = 100.0, exaxis_pos = [0.0,0.0,0.0,0.0], blendT = -1.0, offset_flag = 0, offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]):
        '''
        '''
        self.motion_stop = self.com.StopMotion
        ierr = self.com.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
        if ierr:
            self.motion_stop()
            print(ierr)
            return True

        self.motion_stop = None
        return False
    
    def square(self, dist):

        self._incriment_move(0, dist, 0)
        self._incriment_move(0, 0, dist)
        self._incriment_move(0, -dist, 0)
        self._incriment_move(0, 0, -dist)


    def _get_tool_position(self):
        ierr, tcp_pose = self.com.GetActualTCPPose()
        return tcp_pose

    def _get_joint_angles(self, degrees=True, flag=1):
        if degrees:
            joint_pos = self.com.GetActualJointPosDegree(flag)
        else:
            joint_pos = self.com.GetActualJointPosRadian(flag)
        if isinstance(joint_pos, int):
            return 0, 0, 0, 0, 0, 0
        return joint_pos[1]

    def _invk(self, x, y, z, rx, ry, rz, type=0):
        '''
        Perform inverse Kinematics for the tool to reach a certain position at a certain angle.

        type:
         0-absolute position (base coordinate system)
         1-relative position (base coordinate system)
         2-relative position (tool coordinate system)

        returns:
         [j1,j2,j3,j4,j5,j6]: inverse kinematics solution, Cartesian positional solution for joint positions
        '''
        ierr, join_pos = self.com.GetInverseKin(type, [x, y, z, rx, ry, rz], -1)
        #ierr, join_pos = self.com.GetInverseKinRef(type, [x, y, z, rx, ry, rz], joint_ref) # Might need
        if ierr:
            print(f'ERROR: {ierr}')
        return join_pos

class LightSensor():
    def __init__(self, freq=5000):
        self.freq = freq
        self.lq = LabQuest()
        self.status = -1
        self.rec = False
        

    def connect(self):
        self.status = self.lq.open()
        self.lq.select_sensors(ch1="lq_sensor")
        return self.status

    def close(self):
        self.lq.stop()
        self.lq.close()

    def start(self, freq=5000):
        self.freq = freq
        self.lq.start(period = int(1/self.freq*1000))
    
    def _avg(self, lux:list[float]):
        return sum(lux)/len(lux)
    
    def get(self, avgn=1, N=None, read_time=None, linedata=None):
        '''
        Get sample of size N over avgn readings per sample returned
        '''
        lux=[]
        t=[]
        assert N or read_time

        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))
        if N:
            for n in range(N):
                reading = self.lq.read_multi_pt('ch1', avgn)
                lux.append(self._avg(reading if reading else [0]))
                t.append(1/self.freq*n*avgn)
        elif read_time:
            start_time = time.time()
            while time.time() - start_time < read_time:
                reading = self.lq.read_multi_pt('ch1', avgn)
                lux.append(self._avg(reading if reading else [0]))
                t.append(time.time()-start_time)

        self._plot_points(t, lux, linedata)
        self.rec = False
        return (t, lux)

    def test(self, avgn=1, chunk=1000, button:Button=None, linedata=None):
        if button:
            button.configure(state=DISABLED)

        t, lux = self.get(avgn, read_time=chunk/1000, linedata=linedata)
        le, c, re = self._find_edges(t, lux)

        if button:
            button.configure(state=NORMAL)
        print(f'Left: {le}, center: {c}, Right: {re}')
        return t, lux, le, c, re
        
    def _find_edges(self, times:list[float], lux: list[float]):
        assert len(times) == len(lux)

        peak = lux.index(max(lux))
        threshold = (max(lux) + min(lux)) / 2
        left_edge = right_edge = None
        for i in range(peak, 0, -1):
            if (lux[i - 1] - threshold) * (lux[i] - threshold) <= 0:
                left_edge = self.crossing(times[i - 1], lux[i - 1], times[i], lux[i], threshold)
                break

            for i in range(peak, len(lux) - 1):
                if (lux[i] - threshold) * (lux[i + 1] - threshold) <= 0:
                    right_edge = self.crossing(times[i], lux[i], times[i + 1], lux[i + 1], threshold)
                    break
        
        if left_edge is None or right_edge is None:
            center = None
            print("No two threshold crossings found.")
        else:
            center = (left_edge + right_edge) / 2
        return left_edge, center, right_edge 

    def crossing(self, x1, y1, x2, y2, level):
        if y1 == y2:
            return x1
        return x1 + (level - y1) * (x2 - x1) / (y2 - y1)

    def _plot_points(self, t:list[float], lux:list[float], linedata: tuple[FigureCanvasTkAgg, axes.Axes, Line2D]=None):
        
        if linedata is None:
            return
        canvas, ax, line = linedata
        line.set_xdata(t)
        line.set_ydata(lux)
        ax.relim()
        ax.autoscale_view()
        canvas.draw_idle()

def square_move(step, length):
    moves = []

    steps_per_side = int(length / step) #Number of Times to Increment per Side

    #Define Movement Vectors (x and z)
    pos_x = np.array([step, 0, 0])
    neg_x = np.array([-step, 0, 0])
    pos_z = np.array([0, 0, step])
    neg_z = np.array([0, 0, -step])

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", neg_x), ("-z", neg_z)]

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {steps_per_side} times")

    for name, direction in directions:
        for _ in range(steps_per_side):
            moves.append((name, direction))

    return moves

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    fr5 = RobotCommunicator()
    sensor = LightSensor() #STC
    
    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Path
    step = 1 #STC
    length = 5 #mm
    square_path = square_move(step, length)

    x, z = 0, 0     #Track (x,z)
    data = []       #(x,z,intensity)

    #Move and Scan In Square Path
    for direction_name, move_vec in square_path:
        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #STC: Move Real Robot 
        #fr5._incriment_move(dx, dy, dz)
        fr5.moveL(dx,dy,dz)

        ##Update (xz Plane)
        x += dx
        z += dz

        #STC: Read Real Sensor
        intensity = sensor.get()

        print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")

        data.append((len(data), x, z, intensity)) #Track (step,x,z,intensity)
    
    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()

    return 0