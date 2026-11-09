import logging
import threading
import tkinter as tk
import time
import queue

import numpy as np

from Robot import RPC
from LightSensor import SensorManager
import settingshandler as settings
import XRBPlotter as plt


class RobotCom(RPC):
    HOME = [90, -45, -135, -90, 90, 0]
    TOOL_RBASE = np.array([0, 180, 180])
    AXIS_LIMIT = [
        (-175, 175),
        (-265, 85),
        (-160, 160),
        (-264, 85), 
        (-175, 175),
        (-175, 175),
    ]

    DH = [
    plt.DenavitHartenbergParameter(1, 0, 0   , 152,  np.pi/2, 4.64 , np.array([-0.19 , -18.28, 2.26  ])),
    plt.DenavitHartenbergParameter(2, 0, -425, 0  , 0       , 10.08, np.array([212.47, 0     , 121.2 ])),
    plt.DenavitHartenbergParameter(3, 0, -395, 0  , 0       , 2.71 , np.array([122.62, 0.17  , 12.59 ])),
    plt.DenavitHartenbergParameter(4, 0, 0   , 102,  np.pi/2, 1.56 , np.array([0.05  , -2.33 , 14.68 ])),
    plt.DenavitHartenbergParameter(5, 0, 0   , 102, -np.pi/2, 1.56 , np.array([-0.05 , 2.33  , 14.68 ])),
    plt.DenavitHartenbergParameter(6, 0, 0   , 102, 0       , 0.36 , np.array([0.93  , 0.81  , -20.05])),
    ]

    def __init__(self, opts=settings.OptionDict(), ip="192.168.58.2"):
        self.logger = logging.getLogger('Robot Communication')
        
        self.error_label = self.user_input_window = None
        self.opts = opts

        self.plotters: list[plt.Plotter] = []
        self.lines   : list[tuple]       = []

        self._move_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.monitored_threads: set[threading.Thread] = set()

        self.cur_tool = 0
        self.isocenter = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.offsets:list[tuple[str, np.ndarray[float, float]]] = []
        self._end_eff_angle = np.array([0.0, 0.0, 0.0])
        self._internal_position = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self._disable_move_widgets: list[tk.BaseWidget] = []

        self.set_widget_statuses(False)

        self._default_options()
        
        threading.Thread(target=self.startup, args=(ip,), daemon=True).start()
        #threading.Thread(target=self._status_check, args=(root,), daemon=True).start()
        self.action_queue:queue.Queue[tuple[object, threading.Event]] = queue.Queue()
        
        threading.Thread(target=self._queue_runner, name='robot movement queue',daemon=True).start()

    def startup(self, ip):
        self.logger.info('Connecting to Farino FR5')
        RPC.__init__(self, ip)

        while not self.is_connected():
            self.reconnect()

        self.set_isocenter(*self._get_tool_position())

        end_effector_offset = np.array([0.0, 0.0, 0.0])

        # Change current tool
        self.cur_tool = 2

        # Set tool coordinate frame to match the 
        self.SetToolCoord(self.cur_tool, [*end_effector_offset, *self.TOOL_RBASE], 0, 0, 0, 0)
        self.SetToolList(self.cur_tool , [*end_effector_offset, *self.TOOL_RBASE], 0, 0, 0)

        self.set_widget_statuses(True)
        
    def offset_add(self, reason, x=0.0, y=0.0, z=0.0, drx=0.0, dry=0.0, drz=0.0):
        """Add an offset to future movements"""
        self.offsets.append((reason, np.array([x, y, z, drx, dry, drz]))) 

    @property
    def offset(self):
        cur_offset = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        for reason, offset in self.offsets:
            cur_offset += offset
        return cur_offset 

    def get_prev_test_offset(self, reason):
        cur_offset = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        for key, offset in self.offsets:
            if reason == key:
                cur_offset += offset

        return cur_offset

    def get_prev_test_offset_list(self, reason):
        prev_offsets = []
        for key, offset in self.offsets:
            if reason == key:
                prev_offsets.append(offset)
                
        return prev_offsets

    def set_end_effector_angle(self, rx, ry, rz):
        """Sets end effector angle"""
        self._end_eff_angle = np.array([rx, ry, rz])

    @property
    def end_effector_angle(self):
        """Set effector angle + internal offsets"""
        return self._end_eff_angle + self.offset[3:]

    def set_widget_statuses(self, state:bool):
        """Toggle the status of widgets registered to be disabled during movement commands"""
        set_state = tk.NORMAL if state else tk.DISABLED
        for widget in self._disable_move_widgets:
            widget.configure(state=set_state)

    def register_thread(self):
        """Add current thread to threads that """
        self.monitored_threads.add(threading.current_thread())

    def interrupt_threads(self):

        interrupt_self = threading.current_thread() in self.monitored_threads

        # Set event to let threads know to stop moving
        #self._stop_event.set()

        # Remove all threads allowed to perform movement functions
        self.monitored_threads.clear()

        threading.Thread(target=self.stop, daemon=True, name='Stop').start()
        
        #for thread in list(self.monitored_threads):
        #    # If the current thread that called this function is also being monitored
        #    # Interrupt thread at the end of this function instead on waiting on itself
        #    if thread is current_thread:
        #        interrupt_self = True
        #    else:
        #        print(f'Waiting on thread: {thread.name}')
        #        start_time = time.time()
        #        while thread.is_alive() and time.time()-start_time <= 10.0:
        #            time.sleep(0.01)
        #
        #    self.monitored_threads.remove(thread)

        # Clear event
        #self._stop_event.clear()

        # If a monitored thread called this function, interrupt it
        if interrupt_self:
            raise InterruptedError(f'{threading.current_thread().name} was interrupted.')
        
    def is_connected(self):
        try:
            err, [mainerr, suberr] = self.GetRobotErrorCode()
            return True
        except:
            return False

    def _check_stop_interrupt(self):
        current_thread = threading.current_thread()
        print()
        if current_thread.name != 'MainThread' and current_thread not in self.monitored_threads:
            raise InterruptedError(f'{current_thread.name} stopped from stopped event.')

    def _queue_runner(self):
        """Runs movement commands sent to a queue so that the main thread can """
        while True:
            self.set_widget_statuses(True)
            funct, event = self.action_queue.get()
            threading.Thread(target=self.update_live_plots_during_movement, args=(event,), daemon=True, name='UpdateLivePlotters').start()
            self.set_widget_statuses(False)

            result = funct()
            if result:
                self._prompt_error_window(funct, event, result)

            event.set()

            self.update_live_plots()

    def _default_options(self):
        # Default Variables
        section = 'robot.move'
        #self.opts.add_option(section, 'tool', 0   , tk.IntVar()   , display_name='Tool'           , units=None, description='Tool number')
        #self.opts.add_option(section, 'user', 0   , tk.IntVar()   , display_name='User'           , units=None, description='Artifact number')
        self.opts.add_option(section, 'vel' , 10.0 , tk.DoubleVar(), display_name='Velocity'       , units='%', description='Percentage of speed')
        self.opts.add_option(section, 'acc' , 20.0 , tk.DoubleVar(), display_name='Acceleration'   , units='%', description='Percentage of acceleration')
        self.opts.add_option(section, 'ovl' , 100.0, tk.DoubleVar(), display_name='Velocity factor', units='%', description='Velocity scaling factor')

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
        self.interrupt_threads()
        self.move_joint(self.HOME, in_thread=True)
        self.SetToolCoord(0, [0.0,0.0,0.0, *self.TOOL_RBASE], 0, 0, 0, 0)
        

    def _clear_error(self):
        ierr = self.ResetAllError()
        if self.user_input_window:
            self.user_input_window.destroy()
        self.user_input_window = None
        self.error_label = None
    
    def move_increment(self, dx=0.0, dy=0.0, dz=0.0, drx=0.0, dry=0.0, drz=0.0, in_thread=False, move_type='linear'):
        '''
        Move Arm with incremental movements. 

        ref: Movement reference
         0 - joint point movement
         2 - base coordinate system point movement
         4 - tool coordinate system point movement
         8 - workpiece coordinate system point movement

        vel: Velocity - default: 20.0
        
        acc: Acceleration - default: 100.0
        '''
        self._check_stop_interrupt()
        self.SetToolCoord(self.cur_tool, [0., 0., 0., *self.tool_frame], 0, 0, 0, 0)

        desc_pos = self._get_tool_position()
        angle = list(desc_pos[3:])
        desc_pos[3:] = [0.0, 0.0, 0.0]
        offset = np.array([dx, dy, dz, angle[0]+drx, angle[1]+dry, angle[2]+drz])
        self._internal_position = desc_pos+offset
        self.logger.debug(f'Queing incremental Movement {offset} from {desc_pos} to {self._internal_position}')

        section = 'robot.move'
        vel = self.opts.get(section, 'vel').value
        acc = self.opts.get(section, 'acc').value
        ovl = self.opts.get(section, 'ovl').value

        if move_type == 'linear':
            funct = lambda: self.MoveL(
                        desc_pos=desc_pos,
                        tool=self.cur_tool,
                        user=0,
                        joint_pos=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                        vel=vel,
                        acc=acc,
                        ovl=ovl,
                        blendR=-1.0,
                        blendMode=0,
                        exaxis_pos=[0.0, 0.0, 0.0, 0.0],
                        search=0,
                        offset_flag=2,
                        offset_pos=offset,
                        oacc=20.0,
                        velAccParamMode=0,
                        )
        else:
            funct = lambda: self.MoveCart(
                self._internal_position,
                tool           = self.cur_tool,
                user           = 0,
                vel            = vel,
                acc            = acc,
                ovl            = ovl,
                )
        event = threading.Event()
        if in_thread:
            self.action_queue.put((funct, event))
            return event
        result = funct()
        if result:
            result = self._prompt_error_window(funct, event, result)
        return result

    def move_joint(self, joint_pos, in_thread=False):
        self._check_stop_interrupt()
        
        self.logger.debug(f'Queing joint movement to {tuple(joint_pos)}')

        section = 'robot.move'
        vel = self.opts.get(section, 'vel').value
        acc = self.opts.get(section, 'acc').value
        ovl = self.opts.get(section, 'ovl').value
        
        funct = lambda: self.MoveJ(joint_pos,
                    tool=self.cur_tool,
                    user=0,
                    desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0],
                    vel = vel,
                    acc = acc,
                    ovl = ovl,
                    exaxis_pos = [0.0,0.0,0.0,0.0],
                    blendT = -1.0,
                    offset_flag = 0,
                    offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0],
                )
        event = threading.Event()
        if in_thread:
            self.action_queue.put((funct, event))
            return event
        
        result = funct()
        if result:
            result = self._prompt_error_window(funct, event, result)
        return result

    def move_position(self, x, y, z, rx=None, ry=None, rz=None, in_thread=False, move_type='linear'):
        self._check_stop_interrupt()
        
        end_effector_angle = self.end_effector_angle

        rx = end_effector_angle[0] if rx is None else rx
        ry = end_effector_angle[1] if ry is None else ry
        rz = end_effector_angle[2] if rz is None else rz
        
        desc_pos = self.isocenter.copy()
        desc_pos[3:] = [0.0, 0.0, 0.0]
        self._internal_position = np.array([x, y, z, rx, ry, rz])

        self.SetToolCoord(self.cur_tool, [0., 0., 0., *self.tool_frame], 0, 0, 0, 0)

        self.logger.debug(f'Queueing Movement to {desc_pos} and {self._internal_position}')
        
        section = 'robot.move'
        vel = self.opts.get(section, 'vel').value
        acc = self.opts.get(section, 'acc').value
        ovl = self.opts.get(section, 'ovl').value

        if move_type == 'linear':
            funct = lambda: self.MoveL(
                        desc_pos,
                        tool           = self.cur_tool,
                        user           = 0,
                        vel            = vel,
                        acc            = acc,
                        ovl            = ovl,
                        blendR         = -1.0,
                        blendMode      = 0,
                        exaxis_pos     = [0.0, 0.0, 0.0, 0.0],
                        search         = 0,
                        offset_flag    = 2,
                        offset_pos     = self._internal_position,
                        oacc           = 20.0,
                        velAccParamMode= 0,
                        )
        else:
            funct = lambda: self.MoveCart(
                        desc_pos + self._internal_position,
                        tool           = self.cur_tool,
                        user           = 0,
                        vel            = vel,
                        acc            = acc,
                        ovl            = ovl,
                        )
        event = threading.Event()
        if in_thread:
            self.action_queue.put((funct, event))
            return event
        
        result = funct()
        if result:
            result = self._prompt_error_window(funct, event, result)
        return result

    @property
    def tool_frame(self):
        return np.array(self.TOOL_RBASE) + self.offset[3:]
    
    _position_move  = move_position
    _incriment_move = move_increment
    _joint_move     = move_joint

    def move_to_isocenter(self):
        self.logger.info('Moving to isocenter')
        self.stop()
        self.move_position(0.0, 0.0, 0.0, in_thread=True)

    def move_to_home(self):
        self.logger.debug('Moving to home position')
        self.stop()
        self.move_joint(self.HOME, in_thread=True)

    def _get_tool_position(self):
        if self.is_connected():
            ierr, tcp_pose = self.GetActualTCPPose()
        else:
            tcp_pose = self._internal_position
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

    def set_isocenter(self, desc_pos):
        # Save the current isocenter location internally
        self.isocenter = np.array([*desc_pos[:3],*self.end_effector_angle])

        self.logger.info(f'Setting Isocenter to {self.isocenter}')

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

    def _prompt_error_window(self, funct:object, event=threading.Event, errorcode=None):
        return errorcode
        pkg = self.GetRobotRealTimeState()
        state = self.GetRobotEmergencyStopState()

        # Create popup window
        window = tk.Toplevel()

        # Block commands to the main program until this window is closed
        window.grab_set()

        # Create return variable object that can be used to save values inside lambda function
        return_var = tk.Variable(value=errorcode)
        tk.Label(window, text=f'An error occured while trying to run a movement command!\nError code: {errorcode}\nRobot needs to powercycle: {state}').grid(row=0, column=0, sticky=tk.NSEW, columnspan=5)
        
        try_again_button = tk.Button(window, text='Retry', state=tk.DISABLED, command=lambda: 
                                     (
                                    return_var.set(funct()),
                                        (clear_error_button.configure(state=tk.NORMAL), )
                                        if return_var.get() else 
                                        (clear_error_button.configure(state=tk.DISABLED), window.destroy()), 
                                    try_again_button.configure(state=tk.DISABLED)
                                    )
                                     )
        
        clear_error_button = tk.Button(window, text='Clear Error', command=lambda: 
                                       (self._clear_error(),                            # Clear Error
                                        try_again_button.configure(state=tk.NORMAL),    # Allow user to try the function again
                                        clear_error_button.configure(state=tk.DISABLED) # Disable this button, letting the user know that the error was cleared
                                        ))
        clear_error_button.grid(row=1, column=1)
        stop_test_button = tk.Button(window, text='Stop Test', command=lambda: (event.set(),              # Set event so the test thread can be interrupted
                                                             window.destroy())         # Destroy popup window
                                                             )

        # Place buttons
        try_again_button.grid(row=1, column=0)
        clear_error_button.grid(row=1, column=1)
        stop_test_button.grid(row=1, column=2)

        window.protocol('WM_DELETE_WINDOW', lambda: (event.set(), window.destroy()))
        # Wait on user to close window
        window.wait_window()

        # Set event
        if event.is_set():
            # Interrupt test threads.
            self.interrupt_threads()

        # Return value from the movement function
        return return_var.get()


    def _get_incriment_pos(self, dx=0.0, dy=0.0, dz=0.0, drx=0.0, dry=0.0, drz=0.0):
        desc_pos = self._get_tool_position()
        angle = list(desc_pos[3:])
        desc_pos[3:] = [0.0, 0.0, 0.0]
        offset = np.array([dx, dy, dz, angle[0]+drx, angle[1]+dry, angle[2]+drz])
        return desc_pos + offset

    def _get_movement_pos(self, x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0):
        desc_pos = self.isocenter.copy()
        desc_pos[3:] = [0.0, 0.0, 0.0]
        offset = np.array([x, y, z, rx, ry, rz])
        return desc_pos + offset

    def register_live_plotter(self, plotter: plt.Plotter):
        if plotter not in self.plotters:
            joint_pos = self._get_joint_angles(False)
            plot_line, scatter_line = plotter.plot_robot(self.DH, joint_pos, clear=False, update=True)

            self.plotters.append(plotter)
            self.lines.append((plot_line, scatter_line))
            
    def unregister_live_plotter(self, plotter: plt.Plotter):
        if plotter in self.plotters:
            index = self.plotters.index(plotter)
            plotter = self.plotters.pop(index)
            plot_line, scatter_line = self.lines.pop(index)

            try:
                # Remove lines from figure
                plot_line.remove()
                scatter_line.remove()
            except:
                pass

            # Update figure
            plotter.update()

    def update_live_plots_during_movement(self, event:threading.Event):
        while not event.is_set():
            time.sleep(0.25)
            self.update_live_plots()

    def update_live_plots(self):
        if not self.plotters:
            return
        
        joint_pos = self._get_joint_angles(False)
        for plotter, (plot_line, scatter_line) in zip(self.plotters, self.lines):
            plotter.plot_robot(self.DH, joint_pos, plot_line=plot_line, scatter_line=scatter_line, clear=False, update=True,)

    def plot_current_position(self, plotter: plt.Plotter):
        joint_pos = self._get_joint_angles(False)
        plotter.plot_robot(self.DH, joint_pos)

    def plot_new_position(self, new_pos, plotter: plt.Plotter):
        joint_pos = self.GetInverseKin(0, new_pos)
        if isinstance(joint_pos, int):
            return 
        plotter.plot_robot(self.DH, joint_pos)
