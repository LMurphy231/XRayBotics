import os
import sys
import inspect
import logging

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import numpy as np
import xlsxwriter

import RobotCommunicator as rc
import LightSensor as lq
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
        self.current_results = None
        self.loaded_results = []
        self.close_button = tk.Button(self.root, text='Close',)
        self.build()

    def build(self):

        self.test_selection_frame = self._create_test_selection_frame()
        if self.test_selection_frame is not None:
            self.test_selection_frame.grid(row=0, column=0, sticky=tk.NSEW)

        self.comparison_frame = self._create_comparison_frame()
        if self.comparison_frame is not None:
            self.comparison_frame.grid(row=0, column=1, sticky=tk.NSEW)

        self.plotter_frame = self._create_plotter_frame()
        if self.plotter_frame is not None:
            self.plotter_frame.grid(row=0, column=2, sticky=tk.NSEW)

    def register_test_page(self, test_page):
        self.close_button.grid(row=0, column=15, sticky=tk.NE)
        self.close_button.configure(command=lambda: test_page._toggle_results(False))
    
    def update(self, *args, **kwargs):
        return None

    def _create_comparison_frame(self) -> tk.Frame:
        return None
    
    def _create_plotter_frame(self) -> tk.Frame:
        return None

    def _create_test_selection_frame(self) -> tk.Frame:
        test_selection_frame = tk.Frame(self.root)
        self.test_selection = tk.Listbox(test_selection_frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.grid(row=0, column=0, sticky=tk.NSEW)
        self.test_selection.bind('<<ListboxSelect>>', self._change_selected_test)
        return test_selection_frame

    def _change_selected_test(self, event:tk.Event):
        if event is None:
            return
        
        selections = event.widget.curselection()

        test_type, test_name, test_results = self.loaded_results[selections[-1]]
        
        self.update(*test_results)

    def add_test(self, test_type, test_name, test_results):
        self.loaded_results.append((test_type, test_name, test_results))
        self.test_selection.insert(tk.END, test_name)

    def save_results(self, filename=None):
        if filename is None:
            filename = filedialog.asksaveasfilename(title='Save Gravity Test Results', filetypes=(('XRayBotics Results', '*.xrb'),), defaultextension='*.xrb')

        if not filename:
            return

        if self.current_results is None:
            messagebox.showerror(title='No Test Data', message='No test data available!')
            return

        with open(filename, 'wb') as f:
                        
            for test_type, test_name, test_results in self.loaded_results:

                if test_type.lower() == 'gravity':
                    byte_data = _gravity_test_results_file_text(*test_results)
                else:
                    raise ValueError(f'Test type {test_type} not supported to save!')
                
                f.write(byte_data)

    def load_results(self, filename=None):
        if filename is None:
            filename = filedialog.askopenfilename(title=f'Open Test Results', filetypes=(('XRayBotics Results', '*.xrb'),), defaultextension='*.xrb')

        if not filename:
            return
        
        for test_type, test_name, test_results in parse_xrb_file(filename):
            if test_type == 'gravity':
                current_results = _gravity_test_results_file_read(test_results)
            else:
                raise ValueError(f'Test type {test_type} not supported!')
            
            self.add_test(test_type, test_name, current_results)
        self.test_selection.selection_clear(0, tk.END)
        self.test_selection.selection_set(len(self.loaded_results)-1)
        self.test_selection.event_generate("<<ListboxSelect>>")
        
        

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
        tk.Button(plotter_frame, command=self.load_results, text='Load').grid(row=3, column=0)
        return plotter_frame

    def _test_results(self, angle=0.0):
        origin = np.array([0.0, 0.0, 0.0], dtype=float)
        dist = 0.1
        data = []
        angle = np.random.randint(0, 360)
        print(angle)
        position = np.array([0.0, 0.0, 0.0], dtype=float) + origin
        for i in range(1000):
            distance = dist*i
            position = origin + np.array([distance*np.cos(np.deg2rad(angle)), distance* np.sin(np.deg2rad(angle)), 0.0], dtype=float)
            intensity = abs(1/max(1,abs(500-i)))
            
            data.append((np.array(list(position)), distance, intensity))

        self.add_test('gravity', 'demo test', ('demo gravity test', 'left', data))
        self.test_selection.selection_clear(0, tk.END)
        self.test_selection.selection_set(len(self.loaded_results)-1)
        self.test_selection.event_generate("<<ListboxSelect>>")

    def update(self, test_name, side, result_data):
        self.current_results = (test_name, side, result_data)
        position, distance, intensities = map(list, zip(*result_data))
        
        self.plotter2d.clear()
        for i in range(2):
            self.plotter2d.scatter(x=distance[i*(len(distance)//2):(1+i)*(len(distance)//2)], y=intensities[i*(len(distance)//2):(1+i)*(len(distance)//2)])
            
        self.plotter2d._set_axis_limit(xmin=distance[0], xmax=distance[-1], ymin=min(intensities), ymax=max(intensities)*1.05)
        self.plotter2d.update(keep_axis=False)
        

        self.plotter3d.clear()
        x, y, z = map(list, zip(*position))
        self.plotter3d.scatter(x, y, z, c=intensities, cmap='viridis')
        self.plotter3d.update()

        
class TestPage(BasePage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom=None, ls: lq.SensorManager=None, opts:settings.OptionDict=None, description='', results_page:TestResultsPage=None):
        self.name = name
        self.opts = opts
        self.robot = robot
        self.ls = ls
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
            
        tk.Button(header_frame, command=lambda: threading.Thread(target=self.robot.interrupt_threads, daemon=True).start(), text='Stop test',).grid(row=0, column=3)

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
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom, ls: lq.SensorManager, opts:settings.OptionDict):
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
        TestPage.__init__(self, name, _root, robot, ls, opts, description=description, results_page=results_page)
    
    def _default_settings(self):

        section = 'tests.gravity.path'
        self.option_sections.append(section)
        self.opts.add_option(section, 'step_length', 1.0    , tk.DoubleVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        self.opts.add_option(section, 'length'     , 100.0  , tk.DoubleVar(), display_name='Length'     , units='mm' , description='Length of rectangular path.')
        self.opts.add_option(section, 'height'     , 100.0  , tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'side'       , 'right', tk.StringVar(), display_name='Side'       , units=''   , description='Side of the robot that the Gravity Test will perform on.')

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
            side   = self.opts.get(section, 'side').var.get()
        except:
            return

        isocenter = np.array([0.,0.,0.])
        points = LinacTests.create_gravity_test_rectangle_points(self.robot, self.robot.isocenter[:3], length, height, side)
        #points = pr.calculate_four_points_rectangle(isocenter, length, height, 'y','z')
        #points = pr.rotate_points(points, theta, 'y', 'z')

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
        try:
            section = 'tests.gravity.path'
            step_length = self.opts.get(section, 'step_length').var.get()
            length      = self.opts.get(section, 'length').var.get()
            height      = self.opts.get(section, 'height').var.get()
            side        = self.opts.get(section, 'side').var.get()

            
        except:
            return
        
        self.robot.register_thread()
        test_results = LinacTests.gravity_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, side, step_length=step_length, length=length, width=height)
        
        if self.results_page is not None:
            self.results_page.add_test('gravity', 'Gravity Test Official', ('Gravity Test Official', side, test_results))

class CollimatorTest(TestPage):
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, ls: lq.SensorManager, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        TestPage.__init__(self, name, root, robot, ls, opts, description=description)
    
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
        self.opts.add_option(section, 'step_length', 1.0  , tk.DoubleVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        #self.opts.add_option(section, 'length'     , 100.0, tk.DoubleVar(), display_name='Length'     , units='mm' , description='Length of rectangular path.')
        #self.opts.add_option(section, 'height'     , 100.0, tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'umbra'      , 10   , tk.DoubleVar(), display_name='Umbra'      , units='mm' , description='Distance past x1/x2 that robot will scan')
        #self.opts.add_option(section, 'theta'      , 100.0, tk.DoubleVar(), display_name='Theta'      , units='deg', description='Angle of overall path in relation to the Z axis.')

        section = 'tests.collimator.variables'
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold', units='pu', description='Cutoff limit for light intensity readings.')
        self.opts.add_option(section, 'navg'     , 5, tk.IntVar()      , display_name='Sensor Average Readings', units=''  , description='Number of data points recorded at a single point. The average of these points will be returned.')

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

        path_frame = tk.Frame(paramter_frame)
        path_frame.grid(row=0, column=1) 

        section = 'tests.collimator.path'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(path_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(path_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))
                

        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=2) 

        section = 'linac.angles'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(angle_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(angle_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))
        
        return test_demo_frame

    def _update_test_demo(self):

        
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').var.get()
            x2 = self.opts.get(section, 'x2').var.get()
            y1 = self.opts.get(section, 'y1').var.get()
            y2 = self.opts.get(section, 'y2').var.get()

            section = 'tests.collimator.path'
            umbra = self.opts.get(section, 'umbra').var.get()

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').var.get()
            collimator_angle = self.opts.get(section, 'collimator').var.get()
            couch_angle = self.opts.get(section, 'couch').var.get()
        except:
            return
        isocenter = self.robot.isocenter[:3]
        points = LinacTests.create_collimator_test_rectangle_points(self.robot, isocenter, x1, x2, y1, y2, umbra, gantry_angle, collimator_angle, couch_angle)
        #points = pr.calculate_four_points_rectangle(isocenter, x1+x2+umbra, (y1+y2)*2/3, 'y','z')
#
        #points = pr.rotate_points(points, collimator_angle, 'y', 'z')
        #points = pr.rotate_points(points, -gantry_angle, 'x', 'y')

        self.plotter.clear()
        #R = plt.Ry(np.deg2rad(-90))
        #new_points = []
        #for point in points:
        #    new_points.append(plt.rotate_point(point, R))
        #self._plot_light_field(x1, x2, y1, y2, isocenter[2], gantry_angle, collimator_angle)
        self.plotter.plot_shape(self._dummy_light_field(x1, x2, y1, y2, gantry_angle, collimator_angle-couch_angle))
        
        #points = new_points

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

    def start(self):
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').var.get()
            x2 = self.opts.get(section, 'x2').var.get()
            y1 = self.opts.get(section, 'y1').var.get()
            y2 = self.opts.get(section, 'y2').var.get()

            section = 'tests.collimator.path'
            step_length = self.opts.get(section, 'step_length').var.get()
            umbra = self.opts.get(section, 'umbra').var.get()

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').var.get()
            collimator_angle = self.opts.get(section, 'collimator').var.get()
            couch_angle = self.opts.get(section, 'couch').var.get()

            section = 'tests.collimator.variables'
            threshold = self.opts.get(section, 'threshold').var.get()
            Navg = self.opts.get(section, 'navg').var.get()

        except Exception as e:
            logging.critical(f'Could not start Gantry Test:\n{e}')
            raise e
    
        test_results = LinacTests.collimator_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, x1, x2, y1, y2, umbra, 
                                                        threshold, step_length, Navg, collimator_angle, gantry_angle, couch_angle)
            
class GantryTest(TestPage):
    def __init__(self, name, root:tk.Frame, robot:rc.RobotCom, ls: lq.SensorManager, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        TestPage.__init__(self, name, root, robot, ls, opts, description=description)
    
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

        section = 'tests.gantry.path'
        self.opts.add_option(section, 'height'     , 100  , tk.DoubleVar(), display_name='Height'     , units='mm' , description='Height of the path towards the collimator.')
        self.opts.add_option(section, 'step_length', 1.0  , tk.DoubleVar()   , display_name='Step length', units='mm' , description='Distance between data recordings.')
        self.opts.add_option(section, 'umbra'      , 10   , tk.DoubleVar(), display_name='Umbra'      , units='mm' , description='Distance past x1/x2 that robot will scan.')

        section = 'tests.gantry.variables'
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold'        , units='pu', description='Cutoff limit for light intensity readings.')
        self.opts.add_option(section, 'navg'     , 5, tk.IntVar()      , display_name='Sensor Average Readings', units=''  , description='Number of data points recorded at a single point. The average of these points will be returned.')


        self.option_sections.append('linac')
        self.option_sections.append('tests.gantry')

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


        path_frame = tk.Frame(paramter_frame)
        path_frame.grid(row=0, column=1) 
        section = 'tests.gantry.path'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(path_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(path_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))

        angle_frame = tk.Frame(paramter_frame)
        angle_frame.grid(row=0, column=2) 

        section = 'linac.angles'
        for i, option_name in enumerate(self.opts.options(section)):

            option = self.opts.get(section, option_name)
            
            tk.Label(angle_frame, text=f'{option.display_name}:').grid(row=i, column=0)
            tk.Label(angle_frame, textvariable=option.var).grid(row=i, column=1)
            self.traces.append((option.var, lambda option=option: option.var.trace_add('write', lambda *args: self._update_test_demo()), 'write', None))
        
        return test_demo_frame

    def _update_test_demo(self):

        
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').var.get()
            x2 = self.opts.get(section, 'x2').var.get()
            y1 = self.opts.get(section, 'y1').var.get()
            y2 = self.opts.get(section, 'y2').var.get()

            section = 'tests.gantry.path'
            height = self.opts.get(section, 'height').var.get()
            umbra = self.opts.get(section, 'umbra').var.get()

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').var.get()
            collimator_angle = self.opts.get(section, 'collimator').var.get()
            couch_angle = self.opts.get(section, 'couch').var.get()
        except:
            return
        
        isocenter = self.robot.isocenter[:3]
        points = LinacTests.create_gantry_test_rectangle_points(self.robot, isocenter, x1, x2, y1, y2, height, umbra, gantry_angle, collimator_angle, couch_angle)
        #points = pr.calculate_four_points_rectangle(isocenter, x1+x2+umbra, (y1+y2)*2/3, 'y','z')
#
        #points = pr.rotate_points(points, collimator_angle, 'y', 'z')
        #points = pr.rotate_points(points, -gantry_angle, 'x', 'y')

        self.plotter.clear()
        #R = plt.Ry(np.deg2rad(-90))
        #new_points = []
        #for point in points:
        #    new_points.append(plt.rotate_point(point, R))
        #self._plot_light_field(x1, x2, y1, y2, isocenter[2], gantry_angle, collimator_angle)
        self.plotter.plot_shape(self._dummy_light_field(x1, x2, y1, y2, gantry_angle, collimator_angle))
        
        #points = new_points

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

    def start(self):
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').var.get()
            x2 = self.opts.get(section, 'x2').var.get()
            y1 = self.opts.get(section, 'y1').var.get()
            y2 = self.opts.get(section, 'y2').var.get()

            section = 'tests.gantry.path'
            height = self.opts.get(section, 'height').var.get()
            step_length = self.opts.get(section, 'step_length').var.get()
            umbra = self.opts.get(section, 'umbra').var.get()

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').var.get()
            collimator_angle = self.opts.get(section, 'collimator').var.get()
            couch_angle = self.opts.get(section, 'couch').var.get()

            section = 'tests.gantry.variables'
            threshold = self.opts.get(section, 'threshold').var.get()
            Navg = self.opts.get(section, 'navg').var.get()

        except Exception as e:
            logging.critical(f'Could not start Gantry Test:\n{e}')
            raise e
        
        self.robot.register_thread()

        test_results = LinacTests.gantry_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, x1, x2, y1, y2, height, umbra, 
                                                        threshold, step_length, Navg, collimator_angle, gantry_angle, couch_angle)

        test_name = 'Gantry Test'

        if self.results_page is not None:
            self.results_page.add_test('gravity', test_name, (test_name, test_results))
    

INDENT = '\t'
def parse_xrb_file(filename):
    with open(filename, 'rb') as f:
        arr = f.read()

    tests = []
    while arr:
        test_type, arr = _decode_string(arr)
        test_name, arr = _decode_string(arr)
        byte_length, arr = _decode_int(arr)
        test_bytes = arr[:byte_length]
        arr = arr[byte_length:]
        tests.append((test_type, test_name, test_bytes))

    return tests


def _gravity_test_results_file_text(test_name, side, result_data):
    positions, distance, intensities = map(list, zip(*result_data))
    byte_data = b''
    byte_data += _encode_string(test_name)
    byte_data += _encode_string(side)

    # Create numpy array of data
    arr = np.column_stack((positions, distance, intensities))

    byte_data += np.array(list(arr.shape), dtype=np.int64).tobytes()
    byte_data += arr.tobytes()
    
    return _wrap_test_bytes('gravity', test_name, byte_data)

def _gravity_test_results_file_read(arr:bytearray):
    test_name, arr = _decode_string(arr)
    side, arr = _decode_string(arr)

    shape_arr = arr[:16]
    result_data_arr = arr[16:]
    shape = tuple(np.frombuffer(shape_arr, dtype=np.int64))
    restored_1d = np.frombuffer(result_data_arr, dtype=np.float64)
    raw_result_data = restored_1d.reshape(*shape)
    result_data = [raw_result_data[:, :3], raw_result_data[:,3], raw_result_data[:,4]]
    return test_name, side, tuple(zip(*result_data))

def _wrap_test_bytes(test_type, test_name, arr):
    return _encode_string(test_type) + _encode_string(test_name) + _encode_int(len(arr)) + arr

def _encode_string(text:str):
    byte_arr = b''
    byte_arr += _encode_int(len(text))
    byte_arr += text.encode()
    return byte_arr

def _encode_int(value:int):
    return np.array([value], dtype=np.int64).tobytes()

def _decode_string(arr:bytearray):
    length, arr = _decode_int(arr)
    return arr[:length].decode(), arr[length:]

def _decode_int(arr:bytearray):
    value = int().from_bytes(arr[0:8], byteorder='little')
    return value, arr[8:]




def alan_function(filename, index):
    tests = list(parse_xrb_file(filename))
    test_type, test_name, test_results = tests[index]
    print(f'Picking {test_type} test: "{test_name}"')
    if test_type == 'gravity':
        current_results = _gravity_test_results_file_read(test_results)
    else:
        raise ValueError(f'Test type {test_type} not supported!')
    
    return current_results

#test_results = alan_function(r'TestData/Official Gravity/GravityTest1.xrb', 0)
#for pos, distance, intensity in test_results[2]:
#    print(pos, distance, intensity)