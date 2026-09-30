from contextlib import contextmanager
import configparser
import dataclasses
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
import LightSensor as ls
import communications as com
import XRBPlotter as plt
from XRBPlotter import Plotter
from utill import consts
import settingshandler as settings

from AutomatedTests import pathsRemade as pr

if os.path.basename(sys.executable) == 'pythonw.exe':
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

INI = 'xrb.ini'

class TestPage:
    def __init__(self, name, root:tk.Frame, opts:settings.OptionDict=None):
        self.name = name
        self.opts = opts
        self.frame = tk.Frame(root)
        self.frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.option_sections = []
        self.traces = []

        self.winfo_manager = self.frame.winfo_manager()
        self.vars:dict[str, tk.Variable] = {}
        self._default_settings()
        self.build()
        self.hide()
   
    def _create_header_frame(self) -> tk.Frame:
        """Creates frame for page header.
                
        Intended to be overridden in subclasses.

        Default creates a frame that displays test name
        """
        header_frame = tk.Frame(self.frame)
        tk.Label(header_frame, text=self.name).grid(row=0, column=0)
    
        return header_frame

    def _create_input_frame(self) -> tk.Frame:
        """Creates frame for user inputs.ssddw
        
        Intended to be overridden in subclasses.
        """
        input_frame = tk.Frame(self.frame)
        settings_frame = tk.Frame(input_frame)
        settings_frame.grid(row=0, column=0, sticky=tk.NSEW)
        settings.OptionTree(settings_frame, self.opts, self.option_sections)
        return input_frame

    def _create_start_frame(self) -> tk.Frame:
        """Creates frame for starting buttons.
        
        Intended to be overridden in subclasses.

        Default creates button that runs start command with no inputs
        """
        header_frame = tk.Frame(self.frame)
        if self.opts is not None:
            tk.Button(header_frame, command=lambda: self.opts.save(*self.option_sections), text='Save settings').grid(row=0, column=0)
            tk.Button(header_frame, command=self._load_vars, text='Load').grid(row=0, column=1)
        tk.Button(header_frame, command=self.start, text='start').grid(row=0, column=2)
        return header_frame

    def _create_test_demo_frame(self) -> tk.Frame:
        """Creates frame for test demo plotter.
        
        Intended to be overridden in subclasses.

        Default None
        """
        return None

    def _default_settings(self):
        pass
    
    def _load_vars(self):
        for section in self.opts.sections:
            subsections = section.split('.')
            for var in self.opts.options(section):
                _update_var(self.vars, self.opts.get(section, var), subsections+[var,])
            
    def _update_winfo(self):
        self.winfo_manager = self.frame.winfo_manager()
        self.current_winfo = getattr(self.frame, f'{self.winfo_manager}_info')()
    
    def build(self):
        self.header_frame = self._create_header_frame()
        if self.header_frame is not None:
            self.header_frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.input_frame = self._create_input_frame()
        if self.input_frame is not None:
            self.input_frame.grid(row=1, column=0, sticky=tk.NSEW)

        self.start_frame = self._create_start_frame()
        if self.start_frame is not None:
            self.start_frame.grid(row=2, column=0, sticky=tk.NSEW)

        self.test_demo_frame = self._create_test_demo_frame()
        if self.test_demo_frame is not None:
            self.test_demo_frame.grid(row=1, column=1, sticky=tk.NSEW)

    def hide(self):
        self._update_winfo()
        getattr(self.frame, f'{self.winfo_manager}_forget')()
        self._toggle_traces(False)

    def show(self):
        """Re-apply pack, place, or grid function to frame with last saved
        winfo data.
        """
        getattr(self.frame, self.winfo_manager)(self.current_winfo)
        self._toggle_traces(True)

    def start(self):
        """Default start command, has no function.

        Intended to be overridden in subclasses.
        """
        return

    def _toggle_traces(self, enable=False):
        for i, (var, add_trace, trace_type, trace_id) in enumerate(self.traces):

            if enable:
                # trace already exists
                if trace_id is not None:
                    continue
                trace_id = add_trace()
            else:
                # trace already disabled
                if trace_id is None:
                    continue
                var.trace_remove(trace_type, trace_id)
                trace_id = None
                
            self.traces[i] = (var, add_trace, trace_type, trace_id) 


            

    
class SquareTest(TestPage):
    def __init__(self, name, root:tk.Frame, sensor:ls.SensorManager, robot:rc.RobotCom):
        self.root = root
        
        self.robot = robot
        self.sensor = sensor
        TestPage.__init__(self, name, self.root)

    def _create_input_frame(self):
        
        input_frame = tk.LabelFrame(self.frame)
        self.vars['x']           = _quick_test_var(input_frame, 'x'              , 0.0, 1, 0)
        self.vars['y']           = _quick_test_var(input_frame, 'y'              , 0.0, 2, 0)
        self.vars['z']           = _quick_test_var(input_frame, 'z'              , 0.0, 3, 0)
        self.vars['angle']       = _quick_test_var(input_frame, 'angle'          , 0.0, 4, 0)
        self.vars['width']       = _quick_test_var(input_frame, 'width'          , 5.0, 5, 0)
        self.vars['length']      = _quick_test_var(input_frame, 'length'         , 5.0, 6, 0)
        self.vars['step length'] = _quick_test_var(input_frame, 'Step Length'    , 1  , 7, 0)
        self.vars['avg sample']  = _quick_test_var(input_frame, 'Average Samples', 1  , 8, 0)
        return input_frame

    def start(self):
        print(f'Running Ladder with width: {self.vars['width'].get()}')
        threading.Thread(target=self.robot._test_square, 
                         args = (
                            self.sensor, 
                            self.vars['x'].get(), self.vars['y'].get(), self.vars['z'].get(),
                            self.vars['width'].get(), self.vars['length'].get(), self.vars['angle'].get(), self.vars['step length'].get(),
                            self.vars['avg sample'].get()
                                ),
                        ).start()
        
class GravityTest(TestPage):
    def __init__(self, name, root:tk.Frame, opts:settings.OptionDict):
        self.root = root
        TestPage.__init__(self, name, self.root, opts)
    
    def _default_settings(self):

        section = 'tests.gravity.path'
        self.option_sections.append(section)
        self.opts.add_option(section, 'step_length', 1.0  , tk.IntVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        self.opts.add_option(section, 'length'     , 100.0, tk.DoubleVar(), display_name='Length'     , units='mm' , description='Length of rectangular path.')
        self.opts.add_option(section, 'height'     , 100.0, tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'theta'      , 0.0  , tk.DoubleVar(), display_name='Theta'      , units='deg', description='Angle of overall path in relation to the Z axis.')

        section = 'tests.gravity.variables'
        self.option_sections.append(section)
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold', units='pu', description='Cutoff limit for light intensity readings.')


    def _create_test_demo_frame(self) -> tk.Frame:
        test_demo_frame = tk.Frame(self.frame)
        plotter_frame = tk.Frame(test_demo_frame)
        plotter_frame.grid(row=0, column=0)
        self.plotter = plt.Plotter(plotter_frame, projection='3d')

        paramter_frame = tk.LabelFrame(test_demo_frame, text='Parameters', labelanchor=tk.N)
        paramter_frame.grid(row=1, column=0)

        section = 'tests.gravity.path'
        path_frame = tk.Frame(paramter_frame)
        path_frame.grid(row=0, column=0) 
        for i, option_name in enumerate(self.opts.options(section)):
            option = self.opts.get(section, option_name)
            
            tk.Label(path_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(path_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._plot_field()), 'write', None))



        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=1) 

        return test_demo_frame

    def _plot_field(self):

        #try:
            section = 'tests.gravity.path'
            length = self.opts.get(section, 'length').var.get()
            height = self.opts.get(section, 'height').var.get()
            theta  = self.opts.get(section, 'theta').var.get()

            isocenter = np.array([0.,0.,0.])
            points = pr.calculate_four_points_matrix(isocenter, length, height, theta, 'y','z')

            self.plotter.clear()

            self.plotter.scatter(*isocenter)

            prev_point = points[0]
            self.plotter.scatter(*prev_point)
            for point in points[1:]:
                self.plotter.scatter(*point)
                self.plotter.plot(*zip(prev_point, point))
                prev_point = point

            self.plotter._update()
        #except:
        #    pass

class CollimatorTest(TestPage):
    def __init__(self, name, root:tk.Frame, opts:settings.OptionDict):
        self.root = root
        TestPage.__init__(self, name, self.root, opts)
    
    def _default_settings(self):
        section = 'linac.jaws'
        self.opts.add_option(section, 'x1', 10.0  , tk.DoubleVar()   , display_name='X1', units='mm' , description='X1 length of light field at 100 cm')
        self.opts.add_option(section, 'x2', 10.0  , tk.DoubleVar()   , display_name='X2', units='mm' , description='X2 length of light field at 100 cm')
        self.opts.add_option(section, 'y1', 10.0  , tk.DoubleVar()   , display_name='Y1', units='mm' , description='Y1 length of light field at 100 cm')
        self.opts.add_option(section, 'y2', 10.0  , tk.DoubleVar()   , display_name='Y2', units='mm' , description='Y2 length of light field at 100 cm')
        
        section = 'linac.angles'
        self.opts.add_option(section, 'gantry'    , 0.0  , tk.DoubleVar()   , display_name='Gantry angle'    , units='deg' , description='Angle set for the Gantry')
        self.opts.add_option(section, 'collimator', 0.0  , tk.DoubleVar()   , display_name='Collimator angle', units='deg' , description='Angle set for the collimator')
        self.opts.add_option(section, 'Couch'     , 0.0  , tk.DoubleVar()   , display_name='Couch angle'     , units='deg' , description='Angle set for the Couch')

        section = 'tests.collimator.path'
        self.opts.add_option(section, 'step_length', 1.0  , tk.IntVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        self.opts.add_option(section, 'length'     , 100.0, tk.DoubleVar(), display_name='Length'     , units='mm' , description='Length of rectangular path.')
        self.opts.add_option(section, 'height'     , 100.0, tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'theta'      , 100.0, tk.DoubleVar(), display_name='Theta'      , units='deg', description='Angle of overall path in relation to the Z axis.')

        section = 'tests.collimator.variables'
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold', units='pu', description='Cutoff limit for light intensity readings.')

        self.option_sections.append('linac')
        self.option_sections.append('tests.collimator')

    def _create_test_demo_frame(self) -> tk.Frame:
        test_demo_frame = tk.Frame(self.frame)
        plotter_frame = tk.Frame(test_demo_frame)
        plotter_frame.grid(row=0, column=0)
        self.plotter = plt.Plotter(plotter_frame, projection='3d')

        paramter_frame = tk.LabelFrame(test_demo_frame, text='Parameters', labelanchor=tk.N)
        paramter_frame.grid(row=1, column=0)

        section = 'linac.jaws'
        jaw_frame = tk.Frame(paramter_frame)
        jaw_frame.grid(row=0, column=0) 
        for i, option_name in enumerate(self.opts.options(section)):
            option = self.opts.get(section, option_name)
            
            tk.Label(jaw_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(jaw_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._plot_field()), 'write', None))



        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=1) 

        section = 'linac.angles'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(angle_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(angle_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._plot_field()), 'write', None))
        
        return test_demo_frame

    def _plot_field(self):

        section = 'linac.jaws'
        x1 = self.opts.get(section, 'x1').var.get()
        x2 = self.opts.get(section, 'x2').var.get()
        y1 = self.opts.get(section, 'y1').var.get()
        y2 = self.opts.get(section, 'y2').var.get()

        gantry_angle = self.opts.get('linac.angles', 'gantry').var.get()
        collimator_angle = self.opts.get('linac.angles', 'collimator').var.get()
        isocenter = np.array([0.,0.,0.])
        points = pr.calculate_four_points_matrix(isocenter, x1+x2+15, y1+y2+15, gantry_angle, 'y','z')

        self.plotter.clear()
        R = plt.Ry(np.deg2rad(-90))
        new_points = []
        for point in points:
            new_points.append(plt.rotate_point(point, R))
        #self._plot_light_field(x1, x2, y1, y2, isocenter[2], gantry_angle, collimator_angle)
        self.plotter.plot_shape(self._dummy_light_field(x1, x2, y1, y2, gantry_angle, collimator_angle))
        
        points = new_points

        self.plotter.scatter(*isocenter)

        prev_point = points[0]
        self.plotter.scatter(*prev_point)
        for point in points[1:]:
            self.plotter.scatter(*point)
            self.plotter.plot(*zip(prev_point, point))
            prev_point = point

        self.plotter._update()

    def _dummy_light_field(self, x1, x2, y1, y2, gantry_angle, collimator_angle, origin=np.array([0,0,0])):

        rotation_matrix = plt.rotate(plt.Rx(np.deg2rad(gantry_angle)), plt.Rz(np.deg2rad(collimator_angle)))
        p1 = plt.rotate_point(np.array([-x1, -y1, 0.0]), rotation_matrix) + origin
        p2 = plt.rotate_point(np.array([x2, -y1, 0.0]) , rotation_matrix) + origin
        p3 = plt.rotate_point(np.array([x2, y2, 0.0])  , rotation_matrix) + origin
        p4 = plt.rotate_point(np.array([-x1, y2, 0.0]) , rotation_matrix) + origin
        return [p1, p2, p3, p4]
        self.plotter.plot_shape([p1, p2, p3, p4])


    
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

class SettingsWindow:
    def __init__(self, root, opts:settings.OptionDict):
        self.root = root
        self.opts = opts
        self.window = None
        self.section_frame = None

    def save(self, sections):
        for section in sections:
            for option in self.vars[section]:
                self.opts[section][option] = str(self.vars[section][option].get())

        with open(INI, 'w') as f:
            self.opts.write(f)

    def show(self, section='all'):
        if self.window is None:
            self.window = tk.Toplevel(self.root)
        self.window.title(f'{section.capitalize()} Settings')
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._destroy_window) 

        self._build_section(section)
        
    def _destroy_window(self):
        self.section_frame = self.section_frame.grid_forget()
        self.window        = self.window.destroy()

    def _build_section(self, sections:str):
        if isinstance(sections, str):
            
            if sections == 'all': # Add all sections to section list
                sections = tuple(self.opts.sections())
            else: # Only add selected section to section list
                sections = (sections,)
            
        if self.section_frame:
            self.section_frame.grid_forget()
        self.section_frame = tk.Frame(self.window)
        self.section_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.vars = {}
        i = 0
        for section in sections:
            assert section in self.opts.sections(), f'Section {section} not in current settings!'
            tk.Label(self.section_frame, text=f'[{section}]').grid(row=i, column=0)
            for j, option in enumerate(self.opts.options(section)):
                tk.Label(self.section_frame, text=option.capitalize()).grid(row=i+j+1, column=0)
                var = tk.StringVar(value=self.opts.get(section, option))
                tk.Entry(self.section_frame, textvariable=var).grid(row=i+j+1, column=1, sticky=tk.NSEW)
                self.vars.setdefault(section, {})
                self.vars[section][option] = var
            i += j + 1

        tk.Button(self.window, text='Save', command=lambda: self.save(sections)).grid(row=1, column=0)


class GUI:
    def __init__(self, name = 'XRayBotics'):
        self.window = tk.Tk()
        self.window.geometry('1000x500')
        self.name = name
        self.window.title(name)
        self.settings_window = None

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

    def _build(self):
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        self.root = tk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky=tk.NSEW)

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

        text_window_frame = tk.Frame(self.root)
        #text_window_frame.grid(row=1, column=0, sticky=tk.NSEW)
        self._create_text_window(text_window_frame)

        settings_frame = tk.Frame(self.root)
        #settings_frame.grid(row=1, column=1, columnspan=2, sticky=tk.NSEW)
        self._create_options_window(settings_frame)

    def _create_loggers(self):
        self.gui_logger = logging.getLogger('GUI logger')
        self.gui_logger.setLevel(1)
        self.gui_logger.propagate = False


        self.messenger = logging.getLogger('messenger')
        self.messenger.setLevel(1)
        self.messenger.propagate = False

    def _create_plotter_window(self, frame:tk.Frame):
        plotter_notebook = ttk.Notebook(frame)
        plotter_notebook.grid(row=0, column=0, sticky=tk.NSEW)

        plotter_3d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        self.plotter_3d = Plotter(plotter_3d_frame, projection='3d')

        plotter_2d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter_2d = Plotter(plotter_2d_frame)

    def _create_robot_controller(self, frame:tk.Frame):
        self.robot_vars = {}
        coord_move_frame = tk.LabelFrame(frame, text='Coordinate Movement')
        coord_move_frame.grid(row=0,column=0,sticky=tk.NSEW)
        
        increment_move_frame = tk.LabelFrame(frame, text='Incrimental Movement')
        increment_move_frame.grid(row=0,column=1,sticky=tk.NSEW)

        for sub_frame, vars, funct in ((coord_move_frame, ('X', 'Y', 'Z', 'rx', 'ry', 'rz'), self.robot._position_move), (increment_move_frame, ('dx', 'dy', 'dz', 'drx', 'dry', 'drz'), self.robot._incriment_move)):
            for index, var_name in enumerate(vars):
                tk.Label(sub_frame, text=f'{var_name}:').grid(row=index, column=0,sticky=tk.NSEW)
                var = tk.DoubleVar(value=0.0)
                entry = tk.Entry(sub_frame, textvariable=var)
                entry.grid(row=index,column=1,sticky=tk.NSEW, columnspan=2)
                self.robot_vars[var_name.lower()] = {
                    'var'   : var,
                    'widget': entry,
                }
            tk.Button(sub_frame, text='Reset Position', 
                    command= lambda vars=vars: _reset_var(0.0, *(self.robot_vars[var_name.lower()]['var'] for var_name in vars))
                    ).grid(row=6, column=1, sticky=tk.NSEW)
            
            tk.Button(sub_frame, text='Move', 
                        command= lambda vars=vars, funct=funct: funct(
                            **{var_name.lower(): self.robot_vars[var_name.lower()]['var'].get() for var_name in vars},
                            in_thread=True,
                        )
                        ).grid(row=6, column=2, sticky=tk.NSEW)

        tk.Button(frame, text='Stop Robot'   , command = self.robot.stop).grid(row=0, column=2, sticky=tk.NSEW)
        tk.Button(frame, text='Set Isocenter', command = lambda: self.robot.set_isocenter(*self.robot._get_tool_position())).grid(row=0, column=3, sticky=tk.NSEW)
        tk.Button(frame, text='Set Isocenter', command = lambda: self.robot.home()).grid(row=0, column=4, sticky=tk.NSEW)

    def _create_options_window(self, frame:tk.Frame):
        self.option_tree = settings.OptionTree(frame, self.opts)

    def _default_options(self):
        return

    def _create_test_setup(self, frame:tk.Frame):
        self.test_frame = tk.Frame(frame)
        self.test_frame.grid(row=0, column=1, sticky=tk.NSEW)
        
        self.test_types:dict[str, TestPage] = {
            'Ladder'    : SquareTest('SquareTest'        , self.test_frame, self.ls, self.robot),
            'Gravity'   : GravityTest('GravityTest'      , self.test_frame, self.opts),
            'Collimator': CollimatorTest('CollimatorTest', self.test_frame, self.opts),
            
        }
        self.current_test:TestPage = None

        self.test_selection = tk.Listbox(frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.grid(row=0, column=0, sticky=tk.NSEW)
        self.test_selection.bind('<<ListboxSelect>>', self._change_test_page)
        for test in self.test_types:
            self.test_selection.insert(tk.END, test)

    def _create_text_window(self, frame:tk.Frame):

        textbox_notebook = ttk.Notebook(frame, width=450)
        textbox_notebook.grid(row=0, column=0, sticky=tk.NSEW)
        textbox_notebook.columnconfigure(0, weight=1, minsize=100)
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

def _update_var(vars:dict[str, tk.Variable], value, sections=[]):
    if sections[0] not in vars:
        return
    if len(sections) == 1:
        print(sections, vars[sections[0]])
        vars[sections[0]].set(value)
    else:
        _update_var(vars[sections[0]], value, sections[1:])

def _update_opts(vars:dict[str, dict[str, tk.Variable]], opts:settings.OptionDict, sub_sections=[]):
    for section, item in vars.items():
        cur_section = sub_sections + [section,]
        section_name = '.'.join(cur_section[:-1])
        if isinstance(item, dict):
            _update_opts(item, opts, cur_section)
        elif isinstance(item, tk.Variable):
            print(f'Updating: ["{section_name}"]["{section}"] = {item.get()}')
            opts.setdefault(section_name + '.default', {})
            opts[section_name + '.default'][section] = str(item.get())
        else:
            print(f'Updating: ["{section_name}"] = {item}')
            opts.setdefault(section_name + '.default', {})
            opts[section_name + '.default'][section] = str(item)

    with open(INI, 'w') as f:
        opts.write(f)

def _write_to_textbox(textbox:tk.Text, message, endswith='\n'):
    is_at_bottom = textbox.yview()[1] >= 1.0
    textbox.config(state=tk.NORMAL)
    textbox.insert(tk.END, f'{message}{endswith}')
    textbox.config(state=tk.DISABLED)
    if is_at_bottom:
        textbox.see(tk.END)

def _reset_var(value, *vars: tk.Variable):
    for var in vars:
        var.set(value)

# region Quick GUI
def _quick_test_var(frame:tk.Frame, name, default, row, column):
    tk.Label(frame, text=f'{name}:').grid(row=row,column=column)
    if isinstance(default, int):
        var_type = tk.IntVar
    elif isinstance(default, float):
        var_type = tk.DoubleVar
    else:
        var_type = tk.StringVar
    var = var_type(value=default)
    tk.Entry(frame, textvariable=var).grid(row=row,column=column+1)
    return var

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