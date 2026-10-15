import logging
import configparser
import threading
import tkinter as tk
import time
import queue

import numpy as np

from Robot import RPC
from LightSensor import SensorManager
import settingshandler as settings


class RobotCom(RPC):
    HOME = [0, -45, -135, -90, 90, 0]
    AXIS_LIMIT = [
        (-175, 175),
        (-265, 85),
        (-160, 160),
        (-264, 85), 
        (-175, 175),
        (-175, 175),
    ]

    def __init__(self, opts=settings.OptionDict(), ip="192.168.58.2", root:tk.Toplevel=None):
        self.robot_logger = logging.getLogger('robot')
        self.logger = logging.getLogger('GUI logger')
        self.logger.info('Connecting to Farino FR5')
        
        self.error_label = self.user_input_window = None
        self.opts = opts

        self._move_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_threads: set[threading.Thread] = set()
        self.cur_tool = 0
        self.offsets:list[tuple[str, np.ndarray[float, float]]] = []
        self._disable_move_widgets: list[tk.BaseWidget] = []
        
        self._default_options()
        
        threading.Thread(target=RPC.__init__, args=(self, ip), daemon=True).start()
        #threading.Thread(target=self._status_check, args=(root,), daemon=True).start()
        self.move_thread = threading.Thread(target=lambda:None)
        self.action_queue:queue.Queue[tuple[object, threading.Event]] = queue.Queue()
        threading.Thread(target=self._queue_runner, name='robot movement queue',daemon=True).start()

    def offset_add(self, reason, drx=0.0, dry=0.0, drz=0.0):
        self.offsets.append((reason, np.array([drx, dry, drz]))) 

    @property
    def offset(self):
        cur_offset = np.array([0.0, 0.0, 0.0])
        for reason, offset in self.offsets:
            cur_offset += offset
        return cur_offset 

    def set_widget_statuses(self, state:bool):
        set_state = tk.NORMAL if state else tk.DISABLED
        for widget in self._disable_move_widgets:
            widget.configure(state=set_state)

    def register_thread(self):
        self._monitor_threads.add(threading.current_thread())

    def interrupt_threads(self):
        self._stop_event.set()
        self.stop()
        for thread in list(self._monitor_threads):
            thread.join()
            self._monitor_threads.remove(thread)
        self._stop_event.clear()

    def _check_stop_interrupt(self):
        if self._stop_event.is_set():
            
            raise InterruptedError(f'{threading.current_thread().name} stopped from stopped event.')

    def _queue_runner(self):
        while True:
            self.set_widget_statuses(True)
            funct, event = self.action_queue.get()
            self.set_widget_statuses(False)
            print(f'Result: {funct()}')
            event.set()

    def _default_options(self):
        # Default Variables
        section = 'robot.move'
        self.opts.add_option(section, 'tool', 0   , tk.IntVar()   , display_name='Tool'           , units=None, description='Tool number')
        self.opts.add_option(section, 'user', 0   , tk.IntVar()   , display_name='User'           , units=None, description='Artifact number')
        self.opts.add_option(section, 'vel' , 10.0, tk.DoubleVar(), display_name='Velocity'       , units='%', description='Percentage of speed')
        self.opts.add_option(section, 'acc' , 20.0, tk.DoubleVar(), display_name='Acceleration'   , units='%', description='Percentage of acceleration')
        self.opts.add_option(section, 'ovl' , 0   , tk.IntVar()   , display_name='Velocity factor', units='%', description='Velocity scaling factor')

    def _status_check(self, root=None):
        while True:
            try:
                err, [mainerr, suberr] = self.GetRobotErrorCode()

                if self.error_label:
                    self.error_label.configure(text=f'Main Error: {mainerr} Sub Error: {suberr}')

                if root and (mainerr or suberr) and self.user_input_window is None:
                    self.user_input_window = tk.Toplevel(root, takefocus=True)
                    self.user_input_window.geometry("200x100")
                    self.error_label = tk.Label(self.user_input_window, text=f'Main Error: {mainerr} Sub Error: {suberr}')
                    self.error_label.grid(row=0, column=0, sticky=tk.NSEW)
                    tk.Button(self.user_input_window, text='Clear', command=lambda e=None: self._clear_error()).grid(row=1, column=0, sticky=tk.NSEW)
            except TypeError:
                pass
            finally:
                time.sleep(1)

    def home(self):
        self.logger.debug('Moving to home position')
        self.stop()
        self._joint_move(self.HOME)

    def _monitor(self):
        thread = threading.Thread(target=lambda:None)
        while True:
            while thread.is_alive():
                time.sleep(0.01)

            thread = self.action_queue.get()
            thread.start()

    def _clear_error(self):
        ierr = self.ResetAllError()
        if self.user_input_window:
            self.user_input_window.destroy()
        self.user_input_window = None
        self.error_label = None
    
    def _incriment_move(self, dx=0.0, dy=0.0, dz=0.0, drx=0.0, dry=0.0, drz=0.0, ref=4, vel=20.0, acc=100.0, in_thread=False):
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
        self._check_stop_interrupt()
        self.logger.debug(f'Queing Incrimental Movement ({dx}, {dy}, {dz})')
        print(f'Queing Incrimental Movement ({dx}, {dy}, {dz})')
        print(f'Current Position: {self.GetActualTCPPose(0)}')
        #next_pos = self.GetActualTCPPose(0)[1] + np.array([dx, dy, dz, drx, dry, drz])
        #joint_angles = self._invk(*next_pos, self.cur_tool)
        #return self._joint_move(joint_angles, in_thread)
        funct = lambda: self.MoveL(
                    desc_pos=self.GetActualTCPPose(0)[1],
                    tool=0,
                    user=0,
                    joint_pos=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    vel=10.0,
                    acc=20.0,
                    ovl=100.0,
                    blendR=-1.0,
                    blendMode=0,
                    exaxis_pos=[0.0, 0.0, 0.0, 0.0],
                    search=0,
                    offset_flag=2,
                    offset_pos=[dz, dy, dx, drx, dry, drz],
                    oacc=20.0,
                    velAccParamMode=0,
                    )
        if in_thread:
            event = threading.Event()
            self.action_queue.put((funct, event))
            return event
        print(funct())

    def _position_move(self, x, y, z, rx=0.0, ry=0.0, rz=0.0, ref=4, vel=20.0, acc=100.0, in_thread=False):
        self._check_stop_interrupt()
        pos = self.GetActualTCPPose(0)
        if isinstance(pos, int):
            desc_pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        else:
            desc_pos = pos[1]
        #desc_pos = [1]
        #next_pos = np.array([x, y, z, rx, ry, rz])
        #joint_angles = self._invk(*next_pos, self.cur_tool)
        #return self._joint_move(joint_angles, in_thread)
        dpos = [desc_pos[0]-x,desc_pos[3]-y, desc_pos[2]-z,desc_pos[3]-rx,desc_pos[4]-ry,desc_pos[5]-rz] 
        tool=self.cur_tool
        user=0
        vel=10.0
        acc=20.0
        ovl=100.0
        blendR=-1.0
        blendMode=0
        exaxis_pos=[0.0, 0.0, 0.0, 0.0]
        search=0
        offset_flag=2
        offset_pos=dpos
        oacc=20.0
        velAccParamMode=0
        self.logger.debug(f'Queueing Movement to ({x}, {y}, {z})')
        funct = lambda: self.MoveL(desc_pos, tool, user, vel, acc, ovl, blendR, blendMode, exaxis_pos, search, offset_flag, offset_pos, oacc, velAccParamMode)
        if in_thread:
            event = threading.Event()
            self.action_queue.put((funct, event))
            return event
        funct()

    def _joint_move(self, joint_pos, in_thread=False):
        self._check_stop_interrupt()
        tool=0
        user=0
        desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        vel = 20.0
        acc = 0.0
        ovl = 100.0
        exaxis_pos = [0.0,0.0,0.0,0.0]
        blendT = -1.0
        offset_flag = 0
        offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.logger.debug(f'Queing joint movement to {tuple(joint_pos)}')
        funct = lambda: self.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
        if in_thread:
            event = threading.Event()
            self.action_queue.put((funct, event))
            return event
        
        funct()

    def _move_path(self, path, lq:SensorManager):
        recordings = []
        for direction_name, move_vec in path:
            drx, dry, drz = 0.0
            if len(move_vec) == 3:
                dx, dy, dz = move_vec
            elif len(move_vec) == 6:
                dx, dy, dz, drx, dry, drz = move_vec
            else:
                raise ValueError(f'Move Vector recieved an unexpected amount of values {move_vec}')
            
            self.robot_logger.debug('Moving {} ({})'.format(direction_name, '{:>0.3f}'.join(move_vec)))
            move_thread = self._incriment_move(dx, dy, dz, drx, dry, drz)

            time_data, light_data = _record_thread(move_thread, lq)

            recordings.append((time_data, light_data))

        return recordings         
        
    def _get_tool_position(self):
        ierr, tcp_pose = self.GetActualTCPPose()
        return tcp_pose

    def _get_joint_angles(self, degrees=True, flag=1):
        try:
            if degrees:
                joint_pos = self.GetActualJointPosDegree(flag)
            else:
                joint_pos = self.GetActualJointPosRadian(flag)
            if isinstance(joint_pos, int):
                return 0, 0, 0, 0, 0, 0
        except:
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
        ierr, join_pos = self.GetInverseKin(type, [x, y, z, rx, ry, rz], -1)
        if ierr:
            print(f'ERROR: {ierr}')
        return join_pos

    def set_isocenter(self, x, y, z, rx, ry, rz):
        self.isocenter = np.array([x,y,z,rx,ry,rz])
        self.robot_logger.info(f'Setting Isocenter to {self.isocenter}')
        self.cur_tool = 2
        self.SetToolList(self.cur_tool, self.isocenter, 0, 0, 0)
        self.robot_logger.info(f'Done Setting Isocenter to {self.isocenter}')
        self.robot_logger.info(f'{self.GetTCPOffset(0)}')


    def _update_connection(self):
        self.logger.debug(f'Attempting to reconnect to Farino FR5')
        while True:
            if not self.is_conect:
                self.reconnect()     
            else:
                self.logger.debug(f'Robot connection restored')
                return 
            time.sleep(5)

    def stop(self):
        
        while not self.action_queue.empty():
            self.action_queue.get()
        
        self.StopMove()

    def _test_square(self, lq:SensorManager, x1, y1, z, length, width, angle=0.0, step_length=0.001, avg_sample=5):
        print((x1, y1, z))
        #_wait_on_thread(self._position_move(x1, y1, z))
        test_results = []
        x2 = x1 + width* np.cos(angle)
        y2 = y1 + width* np.sin(angle)
        light_data = []
        time_data = []
        pos_data  = []
        print(angle, np.cos(angle), np.sin(angle))
        nsteps = int(width // step_length)
        for i in range(nsteps+1):
            x = x1+(i/nsteps)*width*np.cos(angle)
            y = y1+(i/nsteps)*width*np.sin(angle)
            
            #_wait_on_thread(self._position_move(x, y, z))
            t, ld = lq.read(avg_sample)
            print(i, nsteps, x, y, ld)
            time_data.append(t)
            light_data.append(ld)
            pos_data.append((x, y, z))
        test_results.append((pos_data, time_data, light_data))
        #_wait_on_thread(self._position_move(x2, y2, z))
            

        x3 = x2 + length*np.cos(angle-np.pi/2)
        y3 = y2 + length*np.sin(angle-np.pi/2)
        #_wait_on_thread(self._position_move(x3, y3, z))
        

        x4 = x3 + width*np.cos(angle-np.pi)
        y4 = y3 + width*np.sin(angle-np.pi)
        dist = np.sqrt((x4-x3)**2+(y4-y3)**2)
        nsteps = int(width // step_length)

        light_data = []
        time_data = []
        pos_data  = []
        for i in range(nsteps+1):
            x = x3+(i/nsteps)*width*np.cos(angle)
            y = y3+(i/nsteps)*width*np.sin(angle)
            #_wait_on_thread(self._position_move(x, y, z))
            t, ld = lq.read(avg_sample)
            print(i, nsteps, x, y, ld)
            time_data.append(t)
            light_data.append(ld)
            pos_data.append((x, y, z))
            
        test_results.append((pos_data, time_data, light_data))
        #_wait_on_thread(self._position_move(x4, y4, z))
        print(f'Start: {(x1, y1, z)}')
        print(f'Pos1: {(x2, y2, z)}')
        print(f'Pos2: {(x3, y3, z)}')
        print(f'Pos3: {(x4, y4, z)}')


def _wait_thread_start(thread:threading.Thread, delay=0.001):
    while thread.ident is None:
        time.sleep(delay)

def _wait_on_thread(thread:threading.Thread, delay=0.001):
    while thread.ident is None or thread.is_alive():
        time.sleep(delay)

def _record_thread(thread:threading.Thread, lq:SensorManager, delay=0.001):
    _wait_thread_start(thread, delay)
    with lq.record() as (light_data, time_data):
        _wait_on_thread(thread, delay)
    return time_data, light_data




