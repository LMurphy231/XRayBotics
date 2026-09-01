from contextlib import contextmanager
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
import queue



import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy as np

import RobotCommunicator as rc

import communications as com
from utill import consts


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

class MessageTerminal(logging.Handler):
    def __init__(self, text:tk.Text, level, handlers=[]):
        self.text = text
        self.handlers = handlers
        super().__init__(level)

    def write(self, line):
        for handler in self.handlers:
            handler.write(line)

    def writelines(self, lines):
        for handler in self.handlers:
            handler.writelines(lines)

    def emit(self, record:logging.LogRecord):
        if record.levelno < self.level:
            return
        try:
            msg = self.format(record)
            _write_to_textbox(self.text, msg)
        except Exception:
            self.handleError(record)
    
class GUI:
    def __init__(self, name = 'XRayBotics'):
        self.window = tk.Tk()
        self.name = name
        self.window.title(name)
        self._create_loggers()
        self._create_window()
        
        self.robot = rc.RobotCom()
        self.coms  = com.Communicator(True)

        self.gui_logger.debug(f'Running Mainloop')
        self.window.mainloop()

    def _create_loggers(self):
        self.gui_logger = logging.getLogger('GUI logger')
        self.gui_logger.setLevel(1)
        self.gui_logger.propagate = False


        self.messenger = logging.getLogger('messenger')
        self.messenger.setLevel(1)
        self.messenger.propagate = False

    def _create_window(self):
        self.root = tk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky=tk.NSEW)

        test_setup_frame = tk.Frame(self.root)
        test_setup_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._create_test_setup(test_setup_frame)

        text_window_frame = tk.Frame(self.root)
        text_window_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self._create_text_window(text_window_frame)

        robot_window_frame = tk.Frame(self.root)
        robot_window_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self._create_robot_controller(robot_window_frame)

    def _create_robot_controller(self, frame:tk.Frame):
        self.robot_vars = {}
        coord_move_frame = tk.LabelFrame(frame, text='Coordinate Movement')
        coord_move_frame.grid(row=0,column=0,sticky=tk.NSEW)

        increment_move_frame = tk.LabelFrame(frame, text='Incrimental Movement')
        increment_move_frame.grid(row=1,column=0,sticky=tk.NSEW)

        for frame, vars in ((coord_move_frame, ('X', 'Y', 'Z')), (increment_move_frame, ('dx', 'dy', 'dz'))):
            for index, var_name in enumerate(vars):
                tk.Label(frame, text=f'{var_name}:').grid(row=index, column=0,sticky=tk.NSEW)
                var = tk.DoubleVar(value=0.0)
                entry = tk.Entry(frame, textvariable=var)
                entry.grid(row=index,column=1,sticky=tk.NSEW, columnspan=2)
                self.robot_vars[var_name.lower()] = {
                    'var'   : var,
                    'widget': entry,
                }

        tk.Button(coord_move_frame, text='Reset Position', 
        command= lambda: _reset_var(0.0, *(self.robot_vars[var_name]['var'] for var_name in ('x','y','z')))
        ).grid(row=3, column=1, sticky=tk.NSEW)

        tk.Button(coord_move_frame, text='Move', 
            command= lambda: self.robot._position_move(
                x=self.robot_vars['x']['var'].get(),
                y=self.robot_vars['y']['var'].get(),
                z=self.robot_vars['z']['var'].get(),
            )
            ).grid(row=3, column=2, sticky=tk.NSEW)


        tk.Button(increment_move_frame, text='Reset Position', 
        command= lambda: _reset_var(0.0, *(self.robot_vars[var_name]['var'] for var_name in ('dx','dy','dz')))
        ).grid(row=3, column=1, sticky=tk.NSEW)

        tk.Button(increment_move_frame, text='Move', 
            command= lambda: self.robot._incriment_move(
                dx=self.robot_vars['dx']['var'].get(),
                dy=self.robot_vars['dy']['var'].get(),
                dz=self.robot_vars['dz']['var'].get(),
            )
            ).grid(row=3, column=2, sticky=tk.NSEW)
    
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

    def _create_text_window(self, frame:tk.Frame):

        textbox_notebook = ttk.Notebook(frame)
        textbox_notebook.grid(row=0, column=0, sticky=tk.NSEW)

        debug_frame = tk.Frame(textbox_notebook)
        textbox_notebook.add(debug_frame, text='Messages')


        textbox = tk.Text(debug_frame, state=tk.NORMAL)
        textbox.grid(row=0, column=0, sticky=tk.NSEW)

        message_handler = MessageTerminal(textbox, logging.INFO) 
        message_handler.setFormatter(logging.Formatter('[%(user)s] - %(message)s'))
        self.messenger.addHandler(message_handler)

        message_frame = tk.Frame(textbox_notebook)
        textbox_notebook.add(message_frame, text='Debug')

        textbox2 = tk.Text(message_frame, state=tk.NORMAL)
        textbox2.grid(row=0, column=0, sticky=tk.NSEW)

        self.debug_textbox = MessageTerminal(textbox2, logging.DEBUG) 
        self.debug_textbox.setFormatter(logging.Formatter('[%(threadName)s][%(levelname)s] - %(message)s'))
        self.gui_logger.addHandler(self.debug_textbox)
        
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


def _write_to_textbox(textbox:tk.Text, message, endswith='\n'):
    textbox.config(state=tk.NORMAL)
    textbox.insert(tk.END, f'{message}{endswith}')
    textbox.config(state=tk.DISABLED)

def _reset_var(value, *vars: tk.Variable):
    for var in vars:
        var.set(value)

# region Logging setup
def _create_debug_logger(log_file=None):
    debug_logger = logging.getLogger('Debug Logger')
    debug_logger.setLevel(logging.DEBUG)
    if log_file:
        log_handler = logging.FileHandler(log_file, mode='w' if __name__ == '__main__' else 'a')
        log_handler.setFormatter(logging.Formatter('%(threadName)s - %(name)s - %(levelname)s - %(message)s'))
        debug_logger.addHandler(log_handler)

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(logging.Formatter('%(threadName)s - %(name)s - %(levelname)s - %(message)s'))
    debug_logger.addHandler(stdout)

_create_debug_logger()
    
debug_logger = logging.getLogger('Debug Logger')
debug_logger.propagate = False

if __name__ == '__main__':
    GUI()