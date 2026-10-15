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
from XRBPlotter import Plotter
import settingshandler as settings

from AutomatedTests import pathsRemade as pr

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

class TestPage:
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom=None, opts:settings.OptionDict=None, description=''):
        self.name = name
        self.opts = opts
        self.robot = robot

        self.description = inspect.cleandoc(description)
        root.rowconfigure(0, weight=1)
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
        header_frame.rowconfigure(0, weight=0)
        header_frame.rowconfigure(1, weight=1, minsize=50)
        header_frame.columnconfigure(0, weight=1, minsize=50)
        tk.Label(header_frame, text=self.name, anchor=tk.N).grid(row=0, column=0, sticky=tk.EW)

        text = scrolledtext.ScrolledText(header_frame, wrap=tk.WORD, background=header_frame['bg'])
        text.insert(tk.END, self.description)
        text.configure(state=tk.DISABLED)
        text.grid(row=1,column=0, sticky=tk.NSEW, pady=5, padx=5)


        return header_frame

    def _create_input_frame(self) -> tk.Frame:
        """Creates frame for user inputs.ssddw
        
        Intended to be overridden in subclasses.
        """
        input_frame = tk.Frame(self.frame)
        settings_frame = tk.Frame(input_frame)
        settings_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.option_tree = settings.OptionTree(settings_frame, self.opts, self.option_sections)
        return input_frame

    def _create_start_frame(self) -> tk.Frame:
        """Creates frame for starting buttons.
        
        Intended to be overridden in subclasses.

        Default creates button that runs start command with no inputs
        """
        header_frame = tk.Frame(self.frame)
        if self.opts is not None:
            tk.Button(header_frame, command=self.option_tree.save, text='Save to Default', ).grid(row=0, column=0)
            tk.Button(header_frame, command=self.option_tree.load, text='Load Default', ).grid(row=0, column=1)
        
        start_button = tk.Button(header_frame, command=self.start, text='Start test', )
        start_button.grid(row=0, column=2)
        if self.robot is not None:
            self.robot._disable_move_widgets.append(start_button)
            
        tk.Button(header_frame, command=self.robot.interrupt_threads, text='Stop test',).grid(row=0, column=3)
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
        self.frame.columnconfigure(0, weight=1, minsize=150)

        self.header_frame = self._create_header_frame()
        if self.header_frame is not None:
            self.header_frame.grid(row=0, column=0, sticky=tk.NSEW)
            self.frame.rowconfigure(0, weight=1, minsize=50)

        self.input_frame = self._create_input_frame()
        if self.input_frame is not None:
            self.input_frame.grid(row=1, column=0, sticky=tk.NSEW)
            self.frame.rowconfigure(1, weight=0, minsize=50)

        self.start_frame = self._create_start_frame()
        if self.start_frame is not None:
            self.start_frame.grid(row=2, column=0, sticky=tk.NSEW)
            self.frame.rowconfigure(2, weight=0, minsize=25)

        self.test_demo_frame = self._create_test_demo_frame()
        if self.test_demo_frame is not None:
            self.test_demo_frame.grid(row=0, column=1, rowspan=4, sticky=tk.NSEW)
            self.frame.columnconfigure(1, weight=2, minsize=150)

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
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, sensor:ls.SensorManager):
        self.root = root
        
        self.sensor = sensor
        TestPage.__init__(self, name, self.root, robot)

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
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, opts:settings.OptionDict):
        self.root = root
        description = """
        Description
        ___________
        
        Place self leveling laser to either the left of the right side of the robotic arm.
        Enter which side the robot the laser is on. 
        Turn on the vertical lasers only.
        Enter paramters for the test.

        Press start.
        """
        
        TestPage.__init__(self, name, self.root, robot, opts, description=description)
    
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
        #test_demo_frame.rowconfigure(0, weight=1)
        #test_demo_frame.columnconfigure(0, weight=1)

        plotter_frame = tk.Frame(test_demo_frame)
        plotter_frame.grid(row=0, column=0)
        plotter_frame.rowconfigure(0, weight=1)
        plotter_frame.columnconfigure(0, weight=1)
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
            points = pr.calculate_four_points_rectangle(isocenter, length, height, 'y','z')
            points = pr.rotate_points(points, theta, 'y', 'z')
     
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
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, opts:settings.OptionDict):
        self.root = root
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        TestPage.__init__(self, name, self.root, robot, opts, description=description)
    
    def _default_settings(self):
        section = 'linac.jaws'
        self.opts.add_option(section, 'x1', 10.0  , tk.DoubleVar()   , display_name='X1', units='mm' , description='X1 length of light field at 100 cm')
        self.opts.add_option(section, 'x2', 10.0  , tk.DoubleVar()   , display_name='X2', units='mm' , description='X2 length of light field at 100 cm')
        self.opts.add_option(section, 'y1', 10.0  , tk.DoubleVar()   , display_name='Y1', units='mm' , description='Y1 length of light field at 100 cm')
        self.opts.add_option(section, 'y2', 10.0  , tk.DoubleVar()   , display_name='Y2', units='mm' , description='Y2 length of light field at 100 cm')
        
        section = 'linac.angles'
        self.opts.add_option(section, 'gantry'    , 0.0  , tk.DoubleVar()   , display_name='Gantry angle'    , units='deg' , description='Angle set for the Gantry')
        self.opts.add_option(section, 'collimator', 0.0  , tk.DoubleVar()   , display_name='Collimator angle', units='deg' , description='Angle set for the collimator')
        self.opts.add_option(section, 'couch'     , 0.0  , tk.DoubleVar()   , display_name='Couch angle'     , units='deg' , description='Angle set for the Couch')

        section = 'tests.collimator.path'
        self.opts.add_option(section, 'step_length', 1.0  , tk.IntVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        #self.opts.add_option(section, 'length'     , 100.0, tk.DoubleVar(), display_name='Length'     , units='mm' , description='Length of rectangular path.')
        #self.opts.add_option(section, 'height'     , 100.0, tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'umbra'      , 10   , tk.DoubleVar(), display_name='Umbra'      , units='mm' , description='Distance past x1/x2 that robot will scan')
        #self.opts.add_option(section, 'theta'      , 100.0, tk.DoubleVar(), display_name='Theta'      , units='deg', description='Angle of overall path in relation to the Z axis.')

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

        section = 'tests.collimator.path'
        umbra = self.opts.get(section, 'umbra').var.get()

        gantry_angle = self.opts.get('linac.angles', 'gantry').var.get()
        collimator_angle = self.opts.get('linac.angles', 'collimator').var.get()
        isocenter = np.array([0.,0.,0.])
        points = pr.calculate_four_points_rectangle(isocenter, x1+x2+umbra, (y1+y2)*2/3, 'y','z')

        points = pr.rotate_points(points, collimator_angle, 'y', 'z')
        points = pr.rotate_points(points, -gantry_angle, 'x', 'y')

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
        self.window.geometry('1000x500')
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

    def _create_menu(self):
        self.menubar = tk.Menu(self.window, tearoff=False)

        communications_menu = tk.Menu(self.menubar, tearoff=False)

        communications_menu = tk.Menu(self.menubar, tearoff=False)
        communications_menu.add_command(label="Messages", command=lambda: self.text_window_frame.grid(row=0, column=0, sticky=tk.SE))

        self.menubar.add_cascade(label="View", menu=communications_menu)

        self.window.config(menu=self.menubar)

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
                    tk.Scale(widget, from_=-100.0, to=100.0, orient=tk.HORIZONTAL, width=13, resolution=0.01, variable=var, showvalue=False).grid(row=0, column=1, sticky=tk.NSEW)
                
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
        
        

        tk.Button(button_frame, text='Stop Robot'   , command = self.robot.stop).grid(row=0, column=1, sticky=tk.NSEW)
        isocenter_button = tk.Button(button_frame, text='Set Isocenter', command = lambda: self.robot.set_isocenter(*self.robot._get_tool_position()))
        isocenter_button.grid(row=1, column=1, sticky=tk.NSEW)
        home_button = tk.Button(button_frame, text='Home'         , command = lambda: self.robot.home())
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

    def _create_options_window(self, frame:tk.Frame):
        self.option_tree = settings.OptionTree(frame, self.opts)

    def _default_options(self):
        return

    def _create_test_setup(self, frame:tk.Frame):
        self.test_frame = tk.Frame(frame)
        self.test_frame.grid(row=0, column=1, sticky=tk.NSEW)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=0)
        frame.columnconfigure(1, weight=1)
        self.test_types:dict[str, TestPage] = {
            'Ladder'    : SquareTest('SquareTest'        , self.test_frame, self.robot, self.ls),
            'Gravity'   : GravityTest('GravityTest'      , self.test_frame, self.robot, self.opts),
            'Collimator': CollimatorTest('CollimatorTest', self.test_frame, self.robot, self.opts),
            
        }
        self.current_test:TestPage = None

        self.test_selection = tk.Listbox(frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.grid(row=0, column=0, sticky=tk.NSEW)
        self.test_selection.bind('<<ListboxSelect>>', self._change_test_page)
        for test in self.test_types:
            self.test_selection.insert(tk.END, test)

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
        #print(sections, vars[sections[0]])
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
            #print(f'Updating: ["{section_name}"]["{section}"] = {item.get()}')
            opts.setdefault(section_name + '.default', {})
            opts[section_name + '.default'][section] = str(item.get())
        else:
            #print(f'Updating: ["{section_name}"] = {item}')
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