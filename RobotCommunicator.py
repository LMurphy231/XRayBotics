import logging
import threading
import tkinter as tk
import time
import queue

from Robot import RPC


class RobotCom(RPC):
    HOME = [0, -45, -133.25, -180, -90, 90]

    def __init__(self, ip="192.168.58.2"):
        self.logger = logging.getLogger('GUI logger')
        self.logger.info('Connecting to Farino FR5')
        threading.Thread(target=RPC.__init__, args=(self, ip), daemon=True).start()
        self.move_thread = threading.Thread(target=lambda:None)
        self.action_queue:queue.Queue[threading.Thread] = queue.Queue()

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

    def _incriment_move(self, dx, dy, dz, drx=0.0, dry=0.0, drz=0.0, ref=4, vel=20.0, acc=100.0):
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
        self.logger.debug(f'Queing Incrimental Movement ({dx}, {dy}, {dz})')
        self.action_queue.put(threading.Thread(
            target = lambda: self.MoveL(
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
                ), 
            daemon=True,
            ))

    def _position_move(self, x, y, z, ref=4, vel=20.0, acc=100.0):
        
        desc_pos = self.GetActualTCPPose(0)[1]
        dpos = [desc_pos[0]-x,desc_pos[3]-y, desc_pos[2]-z,0,0,0] 
        desc_pos=self.GetActualTCPPose(0)[1],
        tool=0
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
        self.logger.debug(f'Queing Movement to ({x}, {y}, {z})')
        self.action_queue.put(
            threading.Thread(
                target = lambda: self.MoveL(desc_pos, tool, user, vel, acc, ovl, blendR, blendMode, exaxis_pos, search, offset_flag, offset_pos, oacc, velAccParamMode),
                daemon=True,
                )
            )

    def _joint_move(self, joint_pos):
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
        self.action_queue.put(
            threading.Thread(
                target= lambda: self.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos),
                daemon= True,
            )
        )
    
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
        print('stopping')
        while not self.action_queue.empty():
            self.action_queue.get()
        self.StopMove()
