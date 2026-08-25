import logging
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


import multiprocessing
import requests
import socket
import threading



import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy

from Robot import RPC

from utill import communications
from utill import consts


class RobotCommunicator(RPC):
    HOME = [0, -45, -133.25, -180, -90, 90]

    def __init__(self, ip="192.168.58.2"):
        RPC.__init__(self, ip)
        self.move_thread = threading.Thread(target=lambda:None)
        self.move_loc = threading.Lock()

    def _move_wait(self):
        while self.move_thread.is_alive():
            time.sleep(0.01)

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
        # wait until current movement command is finished

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
        self.move_thread = threading.Thread(target=self._move, args=(funct, ), daemon=True)
        self.move_thread.start()

    def _position_move(self, x, y, z, ref=4, vel=20.0, acc=100.0):

        
        self._move_wait()

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

        funct = lambda: self.MoveL(desc_pos, tool, user, vel, acc, ovl, blendR, blendMode, exaxis_pos, search, offset_flag, offset_pos, oacc, velAccParamMode)
        self.move_thread = threading.Thread(target=self._move, args=(funct, ), daemon=True)
        self.move_thread.start()
 


class TestPage:
    def __init__(self, name, base_frame:tk.Frame):
        self.name = name
        self.base_frame = base_frame
        self.winfo_manager = base_frame.winfo_manager()
        self.hide()
   
    def _create_header_frame(self) -> tk.Frame:
        """Creates frame for page header.
                
        Intended to be overridden in subclasses.

        Default creates a frame that displays test name
        """
        header_frame = tk.Frame(self.base_frame)
        tk.Label(header_frame, text=self.name).grid(row=0, column=0, sticky=tk.NSEW)

        return header_frame

    def _create_input_frame(self) -> tk.Frame:
        """Creates frame for user inputs.
        
        Intended to be overridden in subclasses.
        """
        return None

    def _create_start_frame(self) -> tk.Frame:
        """Creates frame for starting buttons.
        
        Intended to be overridden in subclasses.

        Default creates button that runs start command with no inputs
        """
        header_frame = tk.Frame(self.base_frame)
        tk.Button(header_frame, command=self.start, text='start').grid(row=0, column=0)
        return header_frame

    def _update_winfo(self):
        self.winfo_manager = self.base_frame.winfo_manager()
        self.current_winfo = getattr(self.base_frame, f'{self.winfo_manager}_info')()
    
    def build(self):
        self.header_frame = self._create_header_frame()
        if self.header_frame is not None:
            self.header_frame.grid(row=0, column=0)

        self.input_frame = self._create_input_frame()
        if self.input_frame is not None:
            self.input_frame.grid(row=1, column=0)

        self.start_frame = self._create_start_frame()
        if self.start_frame is not None:
            self.start_frame.grid(row=2, column=0)

    def hide(self):
        self._update_winfo()
        getattr(self.base_frame, f'{self.winfo_manager}_forget')()

    def show(self):
        """Re-apply pack, place, or grid function to frame with last saved
        winfo data.
        """
        getattr(self.base_frame, self.winfo_manager)(self.current_winfo)

    def start(self):
        """Default start command, has no function.

        Intended to be overridden in subclasses.
        """
        return

class LadderTest(TestPage):
    def __init__(self, name, root:tk.Frame):
        self.root = root
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky=tk.NSEW)
        TestPage.__init__(self, name, self.frame)
        self.build()

    def _create_input_frame(self):
        input_frame = tk.LabelFrame(self.frame)
        self.width_var = tk.DoubleVar(value=100.0)
        tk.Entry(input_frame, textvariable=self.width_var).grid(row=1,column=0)
        return input_frame

    def start(self):
        print(f'Running Ladder with width: {self.width_var.get()}')
        
class GravityTest(TestPage):
    def __init__(self, name, root:tk.Frame):
        self.root = root
        self.frame = tk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky=tk.NSEW)
        TestPage.__init__(self, name, self.frame)
        self.build()

    def build(self):
        return super().build()



class GUI:
    def __init__(self, name = 'XRayBotics'):
        self.robot = RobotCommunicator()
        self.window = tk.Tk()
        self.name = name
        self.window.title(name)
        self._create_window()

        self.window.mainloop()

    def _create_window(self):
        self.root = tk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky=tk.NSEW)

        test_setup_frame = tk.Frame(self.root)
        test_setup_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self._create_test_setup(test_setup_frame)
    
    def _create_test_setup(self, frame:tk.Frame):
        self.test_frame = tk.Frame(frame)
        self.test_frame.grid(row=1, column=1, sticky=tk.NSEW)
        
        self.test_types:dict[str, TestPage] = {
            'Ladder' : LadderTest('LadderTest', self.test_frame),
            'Gravity': GravityTest('GravityTest', self.test_frame),
        }
        self.current_test:TestPage = None

        self.test_selection = tk.Listbox(frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.grid(row=1, column=0, sticky=tk.NSEW)
        self.test_selection.bind('<<ListboxSelect>>', self._change_test_page)
        for test in self.test_types:
            self.test_selection.insert(tk.END, test)

    def _change_test_page(self, event:tk.Event):
        if event is None:
            return

        if self.current_test is not None:
            self.current_test.hide()

        selections = event.widget.curselection()
        if not selections:
            self.current_test = None
            return
        
        test_name = list(self.test_types)[selections[-1]]
        test = self.test_types[test_name]

        self.current_test = test
        self.current_test.show()




if __name__ == '__main__':
    GUI()