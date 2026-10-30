from contextlib import contextmanager
import dataclasses
import inspect
import logging
import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import numpy as np

import RobotCommunicator as rc
import LightSensor as ls
import communications as com
import XRBPlotter as plt
import settingshandler as settings
import TestPages as tp

if os.path.basename(sys.executable) == 'pythonw.exe':
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# Styles
def _create_styles(root):
   

    style = ttk.Style()
    #style.theme_use("clam")
    style.configure('Warning.TButton', bordercolor="#FF0000", lightcolor='red', background="white",)
    style.configure('Default.TButton', background="white",)

INI = 'xrb.ini'
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
        self.window.geometry('1500x650')
        self.name = name
        self.window.title(name)
        self.settings_window = None
        _create_styles(self.window)

        # Load options
        self.opts = settings.OptionDict(INI)
        self._default_options()

        self.robot = rc.RobotCom(self.opts, root=self.window)
        self.ls = ls.SensorManager()
        self._create_loggers()
        self._build()
        
        #self.coms  = com.Communicator(True)

        self.gui_logger.debug(f'Running Mainloop')
        self.window.mainloop()
        self.ls.close()

    def _build(self):
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        self.root = tk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky=tk.NSEW)

        self._create_menu()

        self.root.rowconfigure(0, weight=1, minsize=400)
        self.root.rowconfigure(1, weight=1, minsize=150)

        self.root.columnconfigure(0, weight=0, minsize=450)
        self.root.columnconfigure(1, weight=0, minsize=200)
        self.root.columnconfigure(2, weight=1, minsize=200)

        test_setup_frame = tk.Frame(self.root)
        test_setup_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self._create_test_setup(test_setup_frame)

        robot_window_frame = tk.LabelFrame(self.root, text='Robot Controller')
        robot_window_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self._create_robot_controller(robot_window_frame)

        
        plotter_frame = tk.Frame(self.root)
        #plotter_frame.grid(row=0, column=2, sticky=tk.NSEW)
        self._create_plotter_window(plotter_frame)

        self.text_window_frame = tk.PanedWindow(self.window)
        #text_window_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self._create_text_window(self.text_window_frame)

        self.settings_frame = tk.Frame(self.window)
        
        #self._create_option_window(self.settings_frame)
        
    def _create_loggers(self):
        self.gui_logger = logging.getLogger('GUI logger')
        self.gui_logger.setLevel(1)
        self.gui_logger.propagate = False


        self.messenger = logging.getLogger('messenger')
        self.messenger.setLevel(1)
        self.messenger.propagate = False

    def _create_menu(self):
        self.menubar = tk.Menu(self.window, tearoff=False)

        

        # Settings Menu
        settings_menu = tk.Menu(self.menubar, tearoff=False)
        settings_menu.add_command(label="All", command=lambda: self._create_option_window(self.settings_frame, '').grid(row=0, column=0, pady=1,sticky=tk.NSEW))
        settings_menu.add_command(label="Robot", command=lambda: self._create_option_window(self.settings_frame, ['robot',]).grid(row=0, column=0, pady=1,sticky=tk.NSEW))

        # View Menu
        communications_menu = tk.Menu(self.menubar, tearoff=False)
        communications_menu.add_command(label="Messages", command=lambda: self.text_window_frame.grid(row=0, column=0, sticky=tk.SE))

        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        self.menubar.add_cascade(label="View", menu=communications_menu)

        self.window.config(menu=self.menubar)

    def _create_plotter_window(self, frame:tk.Frame):
        plotter_notebook = ttk.Notebook(frame)
        plotter_notebook.grid(row=0, column=0, sticky=tk.NSEW)

        plotter_3d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        self.plotter_3d = plt.Plotter(plotter_3d_frame, projection='3d')

        plotter_2d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter_2d = plt.Plotter(plotter_2d_frame)

    def _create_robot_controller(self, frame:tk.Frame):
        self.robot_vars = {}

        move_type_notebook = ttk.Notebook(frame)
        move_type_notebook.grid(row=0, column=0)


        var_names = ['x', 'y', 'z', 'rx', 'ry', 'rz']
        function_changes = {}

        sub_frame = tk.Frame(move_type_notebook)
        move_type_notebook.add(sub_frame, text='Coordinate Movement')
        for index, var_name in enumerate(var_names):
            tk.Label(sub_frame, text=f'{var_name}:').grid(row=index%3, column=2*(index//3),sticky=tk.NSEW)
            var = tk.DoubleVar(value=0.0)
            entry = tk.Entry(sub_frame, textvariable=var)
            entry.grid(row=index%3,column=1+2*(index//3),sticky=tk.NSEW)
            self.robot_vars[var_name.lower()] = {
                'var'   : var,
                'widget': entry,
            }
        function_changes['Coordinate Movement'] = (
                        lambda var_names=var_names, funct=self.robot._position_move: funct(
                            **{var_name.lower(): self.robot_vars[var_name.lower()]['var'].get() for var_name in var_names},
                            in_thread=True,
                        ),
                        lambda var_names=var_names: _reset_var(0.0, *(self.robot_vars[var_name.lower()]['var'] for var_name in var_names))
                    )


        sub_frame = tk.Frame(move_type_notebook)
        move_type_notebook.add(sub_frame, text='Incrimental Movement')
        minior_frames = (tk.Frame(sub_frame), tk.Frame(sub_frame))
        for index, var_name in enumerate(var_names):
            var_name = f'd{var_name}'
            var = tk.DoubleVar(value=0.0)
            for i, minor_frame in enumerate(minior_frames):
                tk.Label(minor_frame, text=f'{var_name}:').grid(row=index%3, column=2*(index//3),sticky=tk.E)
                if i == 0:
                    widget = tk.Entry(minor_frame, textvariable=var)
                else:
                    widget = tk.Frame(minor_frame)
                    tk.Label(widget, textvariable=var, width=5).grid(row=0, column=0,sticky=tk.EW)
                    tk.Scale(widget, from_=-250.0, to=250.0, orient=tk.HORIZONTAL, width=13, resolution=0.01, variable=var, showvalue=False).grid(row=0, column=1, sticky=tk.NSEW)
                
                widget.grid(row=index%3,column=1+2*(index//3),sticky=tk.NSEW)
                minor_frame.columnconfigure(1+2*(index//3), minsize=75)

            self.robot_vars[var_name.lower()] = {
                'var'   : var,
                'widget': entry,
            }


        bool_var = tk.BooleanVar(value=False)
        tk.Checkbutton(sub_frame, text='Use Slider', variable=bool_var, command=lambda *args, frames=minior_frames, var=bool_var: 
                        frames[0 if var.get() else 1].grid_forget() == 
                        frames[1 if var.get() else 0].grid(row=0, column=0, sticky=tk.NSEW) ==
                        self.gui_logger.debug(f'Now showing {"Sliders" if var.get() else "Entry"} for Incremental Movement')
                        ).grid(row=1, column=0)
        minior_frames[1 if bool_var.get() else 0].grid(row=0, column=0, sticky=tk.NSEW)

        function_changes['Incrimental Movement'] = (
                        lambda var_names=var_names, funct=self.robot._incriment_move: funct(
                            **{f'd{var_name.lower()}': self.robot_vars[f'd{var_name.lower()}']['var'].get() for var_name in var_names},
                            in_thread=True,
                        ),
                        lambda var_names=var_names: _reset_var(0.0, *(self.robot_vars[f'd{var_name.lower()}']['var'] for var_name in var_names))
                    )




        sub_frame = tk.Frame(move_type_notebook)
        move_type_notebook.add(sub_frame, text='Joint Movement')
        minior_frames = (tk.Frame(sub_frame), tk.Frame(sub_frame))
        for index, (set_angle, (min_, max_)) in enumerate(zip(self.robot.HOME, self.robot.AXIS_LIMIT)):
            var_name = f'joint{index}'
            var = tk.DoubleVar(value=set_angle)
            for i, minor_frame in enumerate(minior_frames):
                tk.Label(minor_frame, text=f'{var_name}:').grid(row=index%3, column=2*(index//3),sticky=tk.E)
                if i == 0:
                    widget = tk.Entry(minor_frame, textvariable=var)
                else:
                    widget = tk.Frame(minor_frame)
                    tk.Label(widget, textvariable=var, width=5).grid(row=0, column=0,sticky=tk.EW)
                    tk.Scale(widget, from_=min_, to=max_, orient=tk.HORIZONTAL, width=13, resolution=0.01, variable=var, showvalue=False).grid(row=0, column=1, sticky=tk.NSEW)
                
                widget.grid(row=index%3,column=1+2*(index//3),sticky=tk.NSEW)
                minor_frame.columnconfigure(1+2*(index//3), minsize=75)

            self.robot_vars[var_name.lower()] = {
                'var'   : var,
                'widget': entry,
            }


        bool_var = tk.BooleanVar(value=False)
        tk.Checkbutton(sub_frame, text='Use Slider', variable=bool_var, command=lambda *args, frames=minior_frames, var=bool_var: 
                        frames[0 if var.get() else 1].grid_forget() == 
                        frames[1 if var.get() else 0].grid(row=0, column=0, sticky=tk.NSEW) ==
                        self.gui_logger.debug(f'Now showing {"Sliders" if var.get() else "Entry"} for Joint Movement')
                        ).grid(row=1, column=0)
        minior_frames[1 if bool_var.get() else 0].grid(row=0, column=0, sticky=tk.NSEW)

        function_changes['Joint Movement'] = (
                        lambda funct=self.robot._joint_move: funct(
                            [self.robot_vars[f'joint{i}']['var'].get() for i in range(len(self.robot.HOME))],
                            in_thread=True,
                        ),
                        lambda: [_reset_var(angle, self.robot_vars[f'joint{i}']['var']) for i, angle in enumerate(self.robot.HOME)]
                    )

        button_frame = tk.Frame(frame)
        button_frame.grid(row=0, column=1, sticky=tk.NSEW)

        move_button = tk.Button(button_frame, text='Move')
        move_button.grid(row=0, column=0, sticky=tk.NSEW)
        self.robot._disable_move_widgets.append(move_button)

        reset_var_button = tk.Button(button_frame, text='Reset Position')
        reset_var_button.grid(row=1, column=0, sticky=tk.NSEW)
        
        

        tk.Button(button_frame, text='Stop Robot'   , command = self.robot.interrupt_threads).grid(row=0, column=1, sticky=tk.NSEW)
        tk.Button(button_frame, text='Clear Error'  , command = lambda: print(self.robot.ResetAllError())).grid(row=4, column=1, sticky=tk.NSEW)
        tk.Button(button_frame, text='Got to isocenter'  , command = self.robot.move_to_isocenter).grid(row=1, column=2, sticky=tk.NSEW)
        isocenter_button = tk.Button(button_frame, text='Set Isocenter', command = lambda: self.robot.set_isocenter(*self.robot._get_tool_position()))
        isocenter_button.grid(row=1, column=1, sticky=tk.NSEW)
        home_button = tk.Button(button_frame, text='Home'         , command = lambda: self.robot.move_to_home())
        home_button.grid(row=2, column=1, sticky=tk.NSEW)

        self.robot._disable_move_widgets.extend([home_button, isocenter_button])

        def _change_functions(event:tk.Event):
            if event is None:
                return
            
            widget = event.widget
            tab = widget.tab(widget.select(), "text")
            move_button.configure(     command=function_changes[tab][0])
            reset_var_button.configure(command=function_changes[tab][1])

        move_type_notebook.bind('<<NotebookTabChanged>>', _change_functions)

    def _create_option_window(self, frame:tk.Frame, sections):
        for _, old_widget in list(frame.children.items()):
            old_widget.destroy()

        temp_frame = tk.Frame(frame)
        temp_frame.grid(row=0, column=0, sticky=tk.NSEW)

        option_frame = tk.Frame(temp_frame)
        option_frame.grid(row=0, column=0, sticky=tk.NSEW)

        
        tree_frame = tk.Frame(temp_frame)
        tree_frame.grid(row=1, column=0, sticky=tk.NSEW)
        option_tree = settings.OptionTree(tree_frame, self.opts, sections)

        tk.Button(option_frame, text='Close', command=lambda: temp_frame.destroy() == frame.grid_forget()).grid(row=0, column=0, sticky=tk.NE)

        button_frame = tk.Frame(temp_frame)
        button_frame.grid(row=3, column=0, sticky=tk.NSEW)
        if self.opts is not None:
            tk.Button(button_frame, command=option_tree.save, text='Save to Default', ).grid(row=2, column=0, sticky=tk.W)
            tk.Button(button_frame, command=option_tree.load, text='Load Default',    ).grid(row=2, column=1, sticky=tk.W)

        return frame

    def _default_options(self):
        return

    def _create_test_setup(self, frame:tk.Frame):
        self.test_frame = tk.Frame(frame)
        self.test_frame.grid(row=0, column=1, sticky=tk.NSEW)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.columnconfigure(1, weight=1)
        self.test_types:dict[str, tp.TestPage] = {
            'Gravity'   : tp.GravityTest('Gravity Test'      , self.test_frame, self.robot, self.ls, self.opts),
            'Collimator': tp.CollimatorTest('Collimator Test', self.test_frame, self.robot, self.ls, self.opts),
            'Gantry'    : tp.GantryTest('Gantry Test'        , self.test_frame, self.robot, self.ls, self.opts),
            
        }
        self.current_test:tp.TestPage = None

        self.test_selection = tk.Listbox(frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.grid(row=0, column=0, sticky=tk.NSEW)
        self.test_selection.bind('<<ListboxSelect>>', self._change_test_page)
        for test in self.test_types:
            self.test_selection.insert(tk.END, test)

        self.test_selection.selection_set(0)
        self.test_selection.event_generate("<<ListboxSelect>>")
        
        self.current_test = self.test_types[list(self.test_types.keys())[0]]
        self.current_test.toggle_page(True)
        

    def _create_text_window(self, frame:tk.Frame):
        frame.configure(relief=tk.GROOVE)
        textbox_notebook = ttk.Notebook(frame, width=450)
        textbox_notebook.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
        tk.Button(frame, text='Close', command=lambda: frame.grid_forget()).grid(row=0, column=0, sticky=tk.NE)
        textbox_notebook.columnconfigure(0, weight=1, minsize=100)
        debug_frame = tk.Frame(textbox_notebook)
        textbox_notebook.add(debug_frame, text='Messages')


        textbox = scrolledtext.ScrolledText(debug_frame, state=tk.NORMAL)
        textbox.grid(row=0, column=0, sticky=tk.NSEW)

        message_handler = MessageTerminal(textbox, logging.INFO) 
        message_handler.setFormatter(logging.Formatter('[%(user)s] - %(message)s'))
        self.messenger.addHandler(message_handler)

        message_frame = tk.Frame(textbox_notebook)
        textbox_notebook.add(message_frame, text='Debug')

        textbox2 = scrolledtext.ScrolledText(message_frame, state=tk.NORMAL)
        textbox2.grid(row=0, column=0, sticky=tk.NSEW)

        self.debug_textbox = MessageTerminal(textbox2, logging.DEBUG) 
        self.debug_textbox.setFormatter(logging.Formatter('[%(threadName)s][%(levelname)s] - %(message)s'))
        self.gui_logger.addHandler(self.debug_textbox)
        
    def _change_test_page(self, event:tk.Event):
        if event is None:
            return

        if self.current_test is not None:
            self.current_test.toggle_page(False)

        selections = event.widget.curselection()
        if not selections:
            self.current_test = None
            return
        
        test_name = list(self.test_types)[selections[-1]]
        test = self.test_types[test_name]

        self.current_test = test
        self.current_test.toggle_page(True)

def _write_to_textbox(textbox:tk.Text, message, endswith='\n', end_state=tk.DISABLED):
    is_at_bottom = textbox.yview()[1] >= 1.0
    textbox.config(state=tk.NORMAL)
    textbox.insert(tk.END, f'{message}{endswith}')
    if is_at_bottom:
        textbox.see(tk.END)
    textbox.config(state=end_state)

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