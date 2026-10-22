import os
import sys
import inspect

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import numpy as np

import RobotCommunicator as rc
import LightSensor as ls
import XRBPlotter as plt
import settingshandler as settings
from AutomatedTests import pathsRemade as pr
import linacTestsAutomatedRemade as LinacTests


class BasePage:
    def __init__(self, root:tk.Frame, traces=[], row=0, column=0, sticky=tk.NSEW, **kwargs):
        self.root = root
        self.root.grid(row=row, column=column, sticky=sticky)
        self.traces = traces

        self._update_winfo()
        self.hide()

    def hide(self):
        self._update_winfo()
        getattr(self.root, f'{self.winfo_manager}_forget')()
        self._toggle_traces(False)
        self.state = False

    def show(self):
        """Re-apply pack, place, or grid function to frame with last saved
        winfo data.
        """
        getattr(self.root, self.winfo_manager)(self.current_winfo)
        self._toggle_traces(True)
        self.state = True

    def add_trace(self, var, trace, trace_type, id_):
        self.traces.append((var, trace, trace_type, id_))

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

    def _update_winfo(self):
        self.winfo_manager = self.root.winfo_manager()
        self.current_winfo = getattr(self.root, f'{self.winfo_manager}_info')()
        
class TestResultsPage(BasePage):
    def __init__(self, name, root:tk.Frame, **kwargs):
        BasePage.__init__(self, root, **kwargs)
        self.name = name
        self.kwargs = kwargs
        
        self.close_button = tk.Button(self.root, text='Close',)
        self.build()

    def build(self):
        self.comparison_frame = self._create_comparison_frame()
        if self.comparison_frame is not None:
            self.comparison_frame.grid(row=0, column=1, sticky=tk.NSEW)

        self.plotter_frame = self._create_plotter_frame()
        if self.plotter_frame is not None:
            self.plotter_frame.grid(row=0, column=0, sticky=tk.NSEW)

    def register_test_page(self, test_page):
        self.close_button.grid(row=0, column=15, sticky=tk.NE)
        self.close_button.configure(command=lambda: test_page._toggle_results(False))
    
    def update(self, *args, **kwargs):
        return None

    def _create_comparison_frame(self) -> tk.Frame:
        return None
    
    def _create_plotter_frame(self) -> tk.Frame:
        return None

class GravityTestResultsPage(TestResultsPage):
    def __init__(self, _root):
        TestResultsPage.__init__(self, 'Gravity Test', tk.Frame(_root))

    def _create_comparison_frame(self) -> tk.Frame:
        comparison_frame = tk.Frame(self.root)
        return comparison_frame

    def _create_plotter_frame(self):
        plotter_frame = tk.Frame(self.root)
        plotter_notebook = ttk.Notebook(plotter_frame)
        plotter_notebook.grid(row=0, column=0, sticky=tk.NSEW)

        plotter_2d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter2d = plt.Plotter(plotter_2d_frame, row=0, column=0)
        

        plotter_3d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        self.plotter3d = plt.Plotter(plotter_3d_frame, projection='3d', row=0, column=0)
        tk.Button(plotter_frame, command=self._test_results, text='Test plotters').grid(row=1, column=0)
        tk.Button(plotter_frame, command=self.save_results, text='Save').grid(row=2, column=0)
        return plotter_frame

    def _test_results(self, angle=0.0):
        origin = np.array([0.0, 0.0, 0.0], dtype=float)
        dist = 0.1
        data = []
        position = np.array([0.0, 0.0, 0.0], dtype=float) + origin
        for i in range(1000):
            distance = dist
            position += np.array([distance*np.cos(np.deg2rad(angle)), distance* np.sin(np.deg2rad(angle)), 0.0], dtype=float)
            intensity = abs(1/max(1,abs(500-i)))
            
            data.append((np.array(list(position)), distance*i, intensity))

        self.update('left', data)

    def update(self, side, result_data):
        position, distance, intensities = map(list, zip(*result_data))
        self.plotter2d.clear()
        self.plotter2d.scatter(x=distance, y=intensities)
        self.plotter2d.update()

        self.plotter3d.clear()
        x, y, z = map(list, zip(*position))
        self.plotter3d.scatter(x, y, z, c=intensities, cmap='viridis')
        self.plotter2d.update()

    def save_results(self, filename=None):
        if filename is None:
            filename = filedialog.asksaveasfilename(title='Save Gravity Test Results', filetypes=(('XRayBotics Results', '*.xrb'),), defaultextension='*.xrb')

        if not filename:
            return

class TestPage(BasePage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom=None, opts:settings.OptionDict=None, description='', results_page:TestResultsPage=None):
        self.name = name
        self.opts = opts
        self.robot = robot
        self.results_page = results_page
        
        self.description = inspect.cleandoc(description)
        _root.rowconfigure(0, weight=1)

        self._root = _root
        BasePage.__init__(self, tk.Frame(_root))
        
        self.option_sections = []

        self.vars:dict[str, tk.Variable] = {}
        self._default_settings()
        self.build()
        self._update_test_demo()
    
    def build(self):
        self.root.columnconfigure(0, weight=1, minsize=150)

        self.header_frame = self._create_header_frame()
        if self.header_frame is not None:
            self.header_frame.grid(row=0, column=0, sticky=tk.NSEW)
            self.root.rowconfigure(0, weight=1, minsize=50)

        self.input_frame = self._create_input_frame()
        if self.input_frame is not None:
            self.input_frame.grid(row=1, column=0, sticky=tk.NSEW)
            self.root.rowconfigure(1, weight=0, minsize=50)

        self.start_frame = self._create_start_frame()
        if self.start_frame is not None:
            self.start_frame.grid(row=2, column=0, sticky=tk.NSEW)
            self.root.rowconfigure(2, weight=0, minsize=25)

        self.test_demo_frame = self._create_test_demo_frame()
        if self.test_demo_frame is not None:
            self.test_demo_frame.grid(row=0, column=1, rowspan=4, sticky=tk.NSEW)
            self.root.columnconfigure(1, weight=2, minsize=150)

        if self.results_page is not None:
            self.results_page.register_test_page(self)

    def start(self):
        """Default start command, has no function.

        Intended to be overridden in subclasses.
        """
        return

    def toggle_page(self, state=False):
        if state:
            self.show()
        else:
            if self.state:
                self.hide()

        if self.results_page is not None and self.results_page.state:
            self.results_page.hide()
            
    def _create_header_frame(self) -> tk.Frame:
        """Creates frame for page header.
                
        Intended to be overridden in subclasses.

        Default creates a frame that displays test name
        """
        
        header_frame = tk.Frame(self.root)
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
        input_frame = tk.Frame(self.root)
        settings_frame = tk.Frame(input_frame)
        settings_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.option_tree = settings.OptionTree(settings_frame, self.opts, self.option_sections)
        return input_frame

    def _create_start_frame(self) -> tk.Frame:
        """Creates frame for starting buttons.
        
        Intended to be overridden in subclasses.

        Default creates button that runs start command with no inputs
        """
        header_frame = tk.Frame(self.root)
        if self.opts is not None:
            tk.Button(header_frame, command=self.option_tree.save, text='Save to Default', ).grid(row=0, column=0)
            tk.Button(header_frame, command=self.option_tree.load, text='Load Default', ).grid(row=0, column=1)
        
        start_button = tk.Button(header_frame, command=lambda: threading.Thread(target=self.start, daemon=True).start(), text='Start test', )
        start_button.grid(row=0, column=2)
        if self.robot is not None:
            self.robot._disable_move_widgets.append(start_button)
            
        tk.Button(header_frame, command=self.robot.interrupt_threads, text='Stop test',).grid(row=0, column=3)

        if self.results_page is not None:
            tk.Button(header_frame, command=lambda: self._toggle_results(True), text='View Results',).grid(row=0, column=4)
        
        return header_frame

    def _create_test_demo_frame(self) -> tk.Frame:
        """Creates frame for test demo plotter.
        
        Intended to be overridden in subclasses.

        Default None
        """
        return None

    def _toggle_results(self, state=False):
        if state:
            self.hide()
            self.results_page.show()
        else:
            self.results_page.hide()
            self.show()
            
    def _default_settings(self):
        pass
            
    def _update_test_demo(self):
        return None

class GravityTest(TestPage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Place self leveling laser to either the left of the right side of the robotic arm.
        Enter which side the robot the laser is on. 
        Turn on the vertical lasers only.
        Enter paramters for the test.

        Press start.
        """

        results_page = GravityTestResultsPage(_root)
        TestPage.__init__(self, name, _root, robot, opts, description=description, results_page=results_page)
    
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
        test_demo_frame = tk.Frame(self.root)

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
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))



        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=1) 

        return test_demo_frame

    def _update_test_demo(self):

        try:
            section = 'tests.gravity.path'
            length = self.opts.get(section, 'length').var.get()
            height = self.opts.get(section, 'height').var.get()
            theta  = self.opts.get(section, 'theta').var.get()
        except:
            return

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
        
    def start(self):
        x = 0.0
        y = 0.0
        z = 0.0
        side = 'left'
        length = 100
        width = 100
        self.robot.register_thread()
        step_length = 10
        LinacTests.gravity_test_automated(self.robot, x, y, z, side, step_length=step_length, length=length, width=width)

class CollimatorTest(TestPage):
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        TestPage.__init__(self, name, root, robot, opts, description=description)
    
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
        test_demo_frame = tk.Frame(self.root)
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
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))



        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=1) 

        section = 'linac.angles'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(angle_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(angle_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))
        
        return test_demo_frame

    def _update_test_demo(self):

        section = 'linac.jaws'
        try:
            x1 = self.opts.get(section, 'x1').var.get()
            x2 = self.opts.get(section, 'x2').var.get()
            y1 = self.opts.get(section, 'y1').var.get()
            y2 = self.opts.get(section, 'y2').var.get()

            section = 'tests.collimator.path'
            umbra = self.opts.get(section, 'umbra').var.get()

            gantry_angle = self.opts.get('linac.angles', 'gantry').var.get()
            collimator_angle = self.opts.get('linac.angles', 'collimator').var.get()
        except:
            return
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
