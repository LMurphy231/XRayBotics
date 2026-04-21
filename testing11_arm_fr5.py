import time
import numpy as np
import numpy
from api.farinoAPI.fairino.Robot import *

class RobotCommunicator():
    def __init__(self):
        self.com = RPC()
        
        self.HOME = [0, -45, -133.25, -180, -90, 90]
        self.move_thread = None
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
        def move(dx, dy, dz):
            cur_pose = self.com.GetActualTCPPose(0)[1]
            self.com.MoveL(
            desc_pos=cur_pose,
            tool=0,
            user=0,
            vel=10.0,
            acc=20.0,
            ovl=100.0,
            blendR=-1.0,
            blendMode=0,
            exaxis_pos=[0.0, 0.0, 0.0, 0.0],
            search=0,
            offset_flag=2,
            offset_pos=[dz, dy, dx, 0.0, 0.0, 0.0],
            oacc=20.0,
            velAccParamMode=0,
            )
            self.move_thread = None
        
        self._move_wait()
        self.move_thread = threading.Thread(target=move, args=(dx, dy, dz), daemon=True)
        self.move_thread.start()

        #print(f'Moving by {(dx, dy, dz)}')
        #current_pose = numpy.array(self.com.GetActualTCPPose(0)[1])
        #new_pose = current_pose + numpy.array([dx, dy, dz, 0, 0, 0])
        #self._position_move(*new_pose[:3])
        #joint_pos = self._invk(*new_pose, type=0)
        #self._joint_move(joint_pos, tool=0)

    def _position_move(self, x, y, z, ref=4, vel=20.0, acc=100.0, *vars):
        '''
        '''
        def move(new_pose):
            self.com.MoveL(
            desc_pos=new_pose,
            tool=0,
            user=0,
            vel=10.0,
            acc=20.0,
            ovl=100.0,
            blendR=-1.0,
            blendMode=0,
            exaxis_pos=[0.0, 0.0, 0.0, 0.0],
            search=0,
            offset_flag=2,
            offset_pos=[0.0, 0.0, 100.0, 0.0, 0.0, 0.0],
            oacc=20.0,
            velAccParamMode=0,
            )
            self.move_thread = None
            
        new_pose = self.com.GetActualTCPPose(0)[1]
        new_pose[:2] = [x, y, z]
        
        self._move_wait()
        self.move_thread = threading.Thread(target=move, args=(new_pose,), daemon=True)
        self.move_thread.start()

        
    
    def home(self):
        self.stop()
        self._joint_move(self.HOME)

    def _joint_move(self, joint_pos, tool=0, user=0, desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0], vel = 20.0, acc = 0.0, 
                    ovl = 100.0, exaxis_pos = [0.0,0.0,0.0,0.0], blendT = -1.0, offset_flag = 0, offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]):
        '''
        '''
        
        def move(joint_pos, tool=0, user=0, desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0], vel = 20.0, acc = 0.0, 
                    ovl = 100.0, exaxis_pos = [0.0,0.0,0.0,0.0], blendT = -1.0, offset_flag = 0, offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]):
            self.com.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
            self.move_thread = None

        self._move_wait()
        self.move_thread = threading.Thread(target=move, args=(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos), daemon=True)
        self.move_thread.start()
        #ierr = self.com.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
        #if ierr:
        #    self.motion_stop()
        #    print(ierr)
        #    return True

        return False
    
    def _move_wait(self):
        while self.move_thread is not None:
            time.sleep(0.01)

    def square(self, dist, event=None):
        if event:
            _toggle_frame(event.widget, DISABLED)
        
        self._incriment_move(0, dist, 0)
        self._move_wait()
        self._incriment_move(0, 0, dist)
        self._move_wait()
        self._incriment_move(0, -dist, 0)
        self._move_wait()
        self._incriment_move(0, 0, -dist)
        
        if event:
            _toggle_frame(event.widget, NORMAL)


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

    def _update_connection(self):
        while True:
            time.sleep(5)
            if not self.com.is_conect:
                self.com.reconnect()
                

    def stop(self):
        print('stopping')
        self.com.StopMove()

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
    
    def get_single(self):
        
        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))

        return self.lq.read('ch1')
    
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
            time.sleep(read_time)
            #while time.time() - start_time < read_time:
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


class dummy_sensor:
    def dummy_light(self):
        return round(np.random.random(),3)

def square_move(step, length):

    half = length/2 #Half Side Movement
    moves = [] #Store Moveset

    steps_full = int(length/step) #Number of Times to Increment for Full Side
    steps_half = int(half/step)

    #Define Movement Vectors (x and z)
    pos_x = np.array([step, 0, 0])
    neg_x = np.array([-step, 0, 0])
    pos_z = np.array([0, 0, step])
    neg_z = np.array([0, 0, -step])

    directions = [("+x", pos_x), ("+z", pos_z), ("-x", neg_x), ("-z", neg_z)]

    print(f"\n[DIRECTIONS] Square-Path Sequence ({length} x {length} mm)")
    for name, vec in directions:
        print(f"  Direction {name}: step {vec}, repeated {steps_full} times")

    for name, direction in directions:
        for _ in range(steps_full):
            moves.append((name, direction))

    return moves


def initial_square(x,y,z,sensor,data, square_path, fr5, home_pos):

    points = 0 #Track Number of Light Points for Initial Scan
    move_data = []
    light_data = []

    #Initial Move and Scan In Square Path
    for direction_name, move_vec in square_path:
        dx, dy, dz = move_vec

        print(f"\n[STEP] Moving {direction_name} by {move_vec}")

        #STC: Move Real Robot 
        #fr5._incriment_move(dx, dy, dz)

        ##Update (xz Plane)
        x += float(dx)
        z += float(dz)

        #STC: Read Real Sensor
        #intensity = sensor.dummy_light()
        intensity = sensor.get()
        threshold = 0.95 #STC

        #Consildated Intensity Value into Single Center-Based Value

        if intensity > threshold: #STC
            points+= 1

        print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")

        data.append((x, z, intensity)) #Track (step,x,z,intensity)

        move_data.append((x, z))
        light_data.append(intensity)

    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()

    print(f"\nMove Data Collected: {move_data}")
    print(f"\nLight Data Collected: {light_data}")
    print(f"\nData Collected: {data}")

    print(f"\nNumber of Light Points Found Past Threshold (Initial Scan): {points}")

    return points


def zero_point(step,sensor,fr5, x,y,z):
    points = 0
    max_z = 50 #cm
    threshold = 0.95
    light_data = []
    hits = []
    inc= step
    it = 0

    print("\nNo Light Points Found in Initial Scan!!!")
    print(f"\nMoving Up Until Light Found or {max_z} mm Above Reached.")

    #Move Up in +z until found light or reach z threshold
    for i in range(max_z):
        z += float(inc) #Update z position

        #fr5._increment_move(0,0,step) #Move
        #intensity = sensor.dummy_light() #STC
        intensity = sensor.get()
        light_data.append(intensity)

        if intensity >= threshold:
            points += 1
            hits.append((z, intensity))
            print(f"-> Position (x,z): ({x}, {z}), Intensity: {intensity:.3f}")
            print("\nBreaking")
            break

        it += 1

    if points == 0: #Move Down now
        pass

    print(f"\nTotal Num of Iterations: {it}")
    print(f"\nNumber of Light Points Found (Zero-Test): {points}")
    print(f"\nHits Collected: {hits}")
    
    return points

def grav_test():
    #Assume all move/scan functions are already implemented
    print("Starting Gravity-Laser Test...")

    fr5 = RobotCommunicator()
    #sensor = dummy_sensor() #STC
    sensor = LightSensor() #STC
    
    #Home Position
    home_pos = fr5.HOME
    print(f"\n[Initialization] Start Position: {home_pos}")
    fr5.home() 

    #Path Paramters
    step = 5 #STC
    length = 10 #mm
    square_path = square_move(step, length)
    x, y, z = float(0), float(0), float(0)     #Track (x,z)
    data = []                                  #(x,z,intensity)

    #Start Initial Scan
    points = initial_square(x,y,z,sensor,data, square_path, fr5, home_pos)
    
    #Scenarios
    if points == 0:
        points = zero_point(step, sensor, fr5, x,y,z)
    

    #Return to Home Position
    print(f"\n[Complete] Return to Home Posiiton: {home_pos}")
    fr5.home()

    return 0


if __name__ == "__main__": 
    grav_test()





    