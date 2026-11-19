import os
import inspect
import logging
import struct
import traceback

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext

import numpy as np
import xlsxwriter
from xlsxwriter import worksheet

import RobotCommunicator as rc
import LightSensor as lq
import XRBPlotter as plt
import settingshandler as settings
import linacTestsAutomatedRemade as LinacTests
import dataProcessing as dp


class BasePage:
    def __init__(self, root:tk.Frame, traces=[], row=0, column=0, sticky=tk.NSEW, **kwargs):
        self.root = root
        self.root.grid(row=row, column=column, sticky=sticky)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
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
    def __init__(self, name, type_, root:tk.Frame, **kwargs):
        BasePage.__init__(self, root, **kwargs)
        self.name = name
        self.type = type_.lower()
        self.kwargs = kwargs
        self.input_frame = None
        self.lines = {}
        self.current_results = None
        self.loaded_results = []
        self.close_button = tk.Button(self.root, text='Close',)
        self.show_edge_var = tk.BooleanVar(value=True)
        self.show_center_var = tk.BooleanVar(value=True)
        self.build()

    def add_test(self, test_type, test_name, test_results, inputs, **extra_data):
        test_type = test_type.lower()
        self.loaded_results.append((test_type, test_name, test_results, inputs, extra_data))
        self.test_selection.insert(tk.END, test_name)

    def build(self):
        self.main_pane = tk.PanedWindow(self.root, orient='horizontal', sashwidth=15)
        self.main_pane.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)
        #self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        left_frame   = tk.PanedWindow(self.main_pane, orient='vertical', sashwidth=15)
        middle_frame = tk.PanedWindow(self.main_pane, orient='vertical', sashwidth=15)
        right_frame  = tk.PanedWindow(self.main_pane, orient='vertical', sashwidth=15)

        self.main_pane.add(left_frame , sticky=tk.NSEW, minsize=150)
        self.main_pane.add(middle_frame , sticky=tk.NSEW, minsize=200)
        self.main_pane.add(right_frame, sticky=tk.NSEW, minsize=500)
        

        self.test_selection_frame = self._create_test_selection_frame(left_frame)
        if self.test_selection_frame is not None:
            left_frame.add(self.test_selection_frame, sticky=tk.NSEW, minsize=125, stretch='never')

        self.comparison_frame = self._create_comparison_frame(middle_frame)
        if self.comparison_frame is not None:
            middle_frame.add(self.comparison_frame, sticky=tk.NSEW, minsize=125, stretch='first')

        self.plotter_frame = self._create_plotter_frame(right_frame)
        if self.plotter_frame is not None:
            right_frame.add(self.plotter_frame, sticky=tk.NSEW, minsize=400, stretch='first')

    def clear_tests(self, indicies=None):
        if indicies is None:
            indicies = list(range(len(self.loaded_results)))

        removed = 0
        for index in sorted(set(indicies)):
           remove_index = index-removed
           self.loaded_results.pop(remove_index)
           self.test_selection.delete(remove_index)
           removed += 1

        self.test_selection.selection_set(len(self.loaded_results)-1)
        self.test_selection.event_generate("<<ListboxSelect>>")

    def register_test_page(self, test_page):
        self.close_button.grid(row=0, column=2, sticky=tk.NE)
        self.close_button.configure(command=lambda: test_page._toggle_results(False))
    
    def update(self, test_type, test_name, raw_data, inputs, extra_data):
        self.current_results = (test_type, test_name, raw_data, inputs, extra_data)

        self.plotter_frame.configure(text=f'{test_type.capitalize()} Results Graph')
        self.plotter2d.grid(True)
        self.plotter3d.grid(True)

        xmin = 0.0
        xmax = 0.0
        ymin = 0.0
        ymax = 0.0

        min_3d = 0.0
        max_3d = 0.0
        
        for i, movement_results in enumerate(raw_data):
            position, distance, intensities = map(list, zip(*movement_results))
            
            label = f'Movement {i}'
            self.lines[label+'2d'] = self.plotter2d.plot(distance, intensities, label=label, marker='o', existing_line=self.lines.get(label+'2d', None))[0]

            x, y, z = map(list, zip(*position))
            self.lines[label+'3d'] = self.plotter3d.scatter(x, y, z, c=intensities, cmap='viridis', label=label, existing_line=self.lines.get(label+'3d', None))

            xmin = min(xmin, distance[0])
            xmax = max(xmax, distance[-1])
            ymin = min(ymin, min(intensities))
            ymax = max(ymax, max(intensities))

            min_3d = min(min_3d, min(x), min(y), min(z))
            max_3d = max(max_3d, max(x), max(y), max(z))

        self.plotter2d._set_axis_limit(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax*1.05)
        offset = 1.25
        dist = max_3d - min_3d
        self.plotter3d._set_axis_limit(xmin=-dist, xmax=dist, ymin=-dist, ymax=dist, zmin=-dist, zmax=dist)
        base_angle = None
        found_angle = None
        try:
            base_angle, notable_data_3d, notable_data_2d, intensities = dp.calculate_angle(raw_data, test_type)

            if self.show_edge_var.get():
                rise1, fall1, c1 = zip(*notable_data_3d)
                label='Rise'
                self.lines[label] = self.plotter3d.scatter(*zip(*rise1), marker = 'x', s=100, c='orange', label=label, existing_line=self.lines.get(label, None))
                label='Fall'  
                self.lines[label] = self.plotter3d.scatter(*zip(*fall1), marker = 'x', s=100, c='pink'  , label=label, existing_line=self.lines.get(label, None))
                label='Center'
                self.lines[label] = self.plotter3d.scatter(*zip(*c1)   , marker = 'x', s=100, c='red'   , label=label, existing_line=self.lines.get(label, None))

            rise1, fall1, c1 = zip(*notable_data_2d)
            for i, (x, center, intensity) in enumerate(zip(zip(rise1, fall1), c1, intensities)):
                label = f'Edges {i}'
                self.lines[label] = self.plotter2d.plot(x, intensity, marker = 'x', markersize=10, label=f'Edges {i}', linewidth=0.0, existing_line=self.lines.get(label, None))[0]
                self.lines[label].set_visible(self.show_edge_var.get())

                label = f'Center {i}'
                self.lines[label] = self.plotter2d.axvline(center, linestyle='--', label=label, existing_line=self.lines.get(label, None))
                self.lines[label].set_visible(self.show_center_var.get())

        except BaseException as e:
            print(traceback.print_exception(e))
            found_angle = str(e)

        self.plotter2d.legend()
        self.plotter2d.label_axis(xlabel='Movement Distance (mm)', ylabel='Light Intensity (lumen)')

        self.plotter2d.legend_update()
        self.plotter3d.legend()
        self.plotter3d.label_axis(xlabel='X (mm)', ylabel='Y (mm)', zlabel='Z (mm)')

        self.plotter2d.update(keep_axis=False)
        self.plotter3d.update(autoscale=True)

        offset = extra_data.get('offset', np.array([0.0]*6))

        
        if base_angle is not None:
            if test_type == 'gravity':
                grav_offset = {
                    'left':  offset[3],
                    'right': -offset[3],
                    'front': offset[4],
                }
                found_angle = base_angle - grav_offset[inputs['side']]
            elif test_type == 'collimator':
                found_angle = base_angle - offset[5]
            elif test_type == 'gantry':
                found_angle = base_angle - offset[4]

        self.update_comparison_frame(base_angle, found_angle, **inputs)

    def update_comparison_frame(self, base_angle, found_angle, **kwargs):

        def create_frame(data, current_id=''):
            for name, value in data.items():

                if isinstance(value, dict):
                    new_id = self.results_tree.insert(current_id, tk.END, text=name, open=True)
                    create_frame(value, new_id)
                else:
                    self.results_tree.insert(current_id, tk.END, text=name, values=[value,], open=True)

        if self.input_frame is not None:
            self.input_frame.destroy()
        
        self.input_frame = tk.Frame(self.comparison_frame, borderwidth=2, relief=tk.GROOVE)
        self.input_frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(self.input_frame, text='Parameters used').pack(side=tk.TOP, expand=False, fill=tk.X)
        self.results_tree = ttk.Treeview(self.input_frame, columns=('Value',), show='tree headings')
        
        self.results_tree.heading("#0", text="Input", anchor="w")
        self.results_tree.column("#0", minwidth=200)
        self.results_tree.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        for i, header in enumerate(('Value',)):
            self.results_tree.heading(header, text=header)
            self.results_tree.column(i, width=100, minwidth=100)

        create_frame(kwargs)

        if isinstance(found_angle, float):
            tk.Label(self.input_frame, text=f'Found Angle: {base_angle:.3f} Degrees').pack()
            tk.Label(self.input_frame, text=f'Found accounting for offsets: {found_angle:.3f} Degrees').pack()
        else:
            tk.Label(self.input_frame, text=f'Unable to calculate angle due to:\n{found_angle}').pack()
                
    def save_results(self, filename=None, tests:list=[]):
        
        if filename is None:
            filename = filedialog.asksaveasfilename(title='Save Test Results', filetypes=(('XRayBotics Results', '*.xrb'),('Excel File', '*.xlsx')), defaultextension='*.xrb')

        if not filename:
            return
        
        if not tests:
            messagebox.showerror(title='No Test Data', message='No test data available!')
            return

        if filename.endswith('.xrb'):
            save_tests_to_xrb(filename, tests)
        elif filename.endswith('.xlsx'):
            save_tests_to_xlsx(filename, tests)
            if messagebox.askyesno(title='Open Excel File', message=f'Do you want to open {filename}?'):
                os.startfile(filename)
        else:
            raise NotImplementedError(f'File type {os.path.splitext(filename)[-1]} not supported')

    def load_results(self, filenames=None):
        if filenames is None:
            filenames = filedialog.askopenfilenames(title=f'Open Test Results', filetypes=(('XRayBotics Results', '*.xrb'),), defaultextension='*.xrb')

        if not filenames:
            return

        if not isinstance(filenames, (tuple, list)):
            filenames = (filenames,)

        for filename in filenames:
            for test_type, test_name, current_results, inputs, extra_data in parse_xrb_file(filename):
                self.add_test(test_type, test_name, current_results, inputs, **extra_data)

        self.test_selection.selection_clear(0, tk.END)
        self.test_selection.selection_set(len(self.loaded_results)-1)
        self.test_selection.event_generate("<<ListboxSelect>>")

    def _create_comparison_frame(self, frame:tk.Frame):
        comparison_frame = tk.Frame(frame)
        return comparison_frame
    
    def _create_plotter_frame(self, frame:tk.Frame):
        plotter_frame = tk.LabelFrame(frame, text='Test Results Graph', font=("Arial", 14, "bold"), labelanchor=tk.N)
        plotter_notebook = ttk.Notebook(plotter_frame)
        plotter_notebook.pack(expand=True, fill=tk.BOTH)

        plotter_2d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter2d = plt.Plotter(plotter_2d_frame, row=0, column=0)

        self.plotter2d.add_menu_option(label='Show Edges', command=lambda: self.update(*self.current_results) if self.current_results else None, var=self.show_edge_var)
        self.plotter2d.add_menu_option(label='Show Centers', command=lambda: self.update(*self.current_results) if self.current_results else None, var=self.show_center_var)

        plotter_3d_frame = tk.Frame(plotter_notebook)
        plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        self.plotter3d = plt.Plotter(plotter_3d_frame, projection='3d', row=0, column=0)

        self.plotter3d.add_menu_option(label='Show Edges', command=lambda: self.update(*self.current_results) if self.current_results else None, var=self.show_edge_var)
        self.plotter3d.add_menu_option(label='Show Centers', command=lambda: self.update(*self.current_results) if self.current_results else None, var=self.show_center_var)
        return plotter_frame

    def _create_test_selection_frame(self, frame:tk.Frame):
        test_selection_frame = tk.Frame(frame)

        tk.Label(test_selection_frame, text='Test Result Selection').pack(side=tk.TOP, expand=False, fill=tk.X)
        self.test_selection = tk.Listbox(test_selection_frame, selectmode=tk.SINGLE, exportselection=False)
        self.test_selection.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.test_selection.bind('<<ListboxSelect>>', self._change_selected_test)

        tk.Button(test_selection_frame, width=20, text='Open'              ,command=self.load_results,).pack(side=tk.TOP, expand=False, fill=None)
        tk.Button(test_selection_frame, width=20, text='Save Tests'        , command=self._prompt_save_window).pack(side=tk.TOP, expand=False, fill=None)
        tk.Button(test_selection_frame, width=20, text='Rename Test'       , command=self._prompt_test_name_change).pack(side=tk.TOP, expand=False, fill=None)
        tk.Button(test_selection_frame, width=20, text='Clear Current Test', command=lambda: self.clear_tests(self.test_selection.curselection())).pack(side=tk.TOP, expand=False, fill=None)

        return test_selection_frame
    
    def _change_selected_test(self, event:tk.Event):
        if event is None:
            return
        
        selections = event.widget.curselection()

        if not selections:
            self.plotter2d.clear()
            self.plotter3d.clear()
            self.plotter2d.update()
            self.plotter3d.update()
            return 
        
        test_type, test_name, raw_data, inputs, extra_data = self.loaded_results[selections[-1]]
        
        self.update(test_type, test_name, raw_data, inputs, extra_data)

    def _prompt_save_window(self):
        window = tk.Toplevel(takefocus=True)
        tk.Label(window, text='Select Tests to save').grid(row=0, column=0, sticky=tk.NSEW)
        window.grab_set()

        test_selection_widget = tk.Listbox(window, selectmode=tk.MULTIPLE, exportselection=False)
        test_selection_widget.grid(row=1, column=0, sticky=tk.NSEW)

        for test in self.loaded_results:
            test_selection_widget.insert(tk.END, test[1])

        button_frame = tk.Frame(window)
        button_frame.grid(row=2, column=0)
        tk.Button(button_frame, text='Clear', command=lambda: test_selection_widget.selection_clear(0, tk.END)).grid(row=0, column=0, sticky=tk.NSEW)
        tk.Button(button_frame, text='Save', command=lambda: self.save_results(tests=[self.loaded_results[index] for index in test_selection_widget.curselection()])==window.destroy()).grid(row=0, column=1, sticky=tk.NSEW)

    def _prompt_test_name_change(self):

        selections = self.test_selection.curselection()
        if not selections:
            return
        index = selections[-1]
        old_test_name = self.loaded_results[index][1]

        window = tk.Toplevel(takefocus=True)
        tk.Label(window, text='Change Test name').grid(row=0, column=0, sticky=tk.NSEW)
        window.grab_set()

        var = tk.StringVar(value=old_test_name)
        entry = tk.Entry(window, textvariable=var)
        entry.grid(row=1, column=0, sticky=tk.NSEW)
        entry.focus_set()
        entry.icursor(tk.END)
        
        tk.Button(window, text='Save', command=lambda: self._rename_test(var.get(), index)==window.destroy()).grid(row=1, column=1, sticky=tk.NSEW)

    def _rename_test(self, new_name:str, index:int):
        test_type, test_name, raw_data, inputs, extra_data = self.loaded_results[index]

        self.loaded_results[index] = (test_type, new_name, tuple(raw_data), inputs, extra_data)

        self.test_selection.delete(index)

        self.test_selection.insert(index, new_name)
        self.test_selection.selection_set(index)

class GravityTestResultsPage(TestResultsPage):
    def __init__(self, _root):
        TestResultsPage.__init__(self, 'Gravity Test', 'gravity', tk.Frame(_root))

class CollimatorTestResultsPage(TestResultsPage):
    def __init__(self, _root):
        TestResultsPage.__init__(self, 'Collimator Test', 'collimator', tk.Frame(_root))

        

class TestPage(BasePage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom=None, ls: lq.SensorManager=None, opts:settings.OptionDict=None, description='', results_page:TestResultsPage=None):
        self.name = name
        self.opts = opts
        self.robot = robot
        self.ls = ls
        self.results_page = results_page

        self.plotter = None
        
        self.description = inspect.cleandoc(description)
        self._root = _root

        BasePage.__init__(self, tk.Frame(_root))
        
        self.option_sections = []

        self.vars:dict[str, tk.Variable] = {}
        self._default_settings()
        self.build()
        self._update_test_demo()
    
    def build(self):
        self.page_frame = tk.PanedWindow(self.root, orient='horizontal', sashwidth=15, height=500)
        self.page_frame.pack(expand=True, fill=tk.BOTH)

        left_frame  = tk.PanedWindow(self.page_frame, orient='vertical', sashwidth=15)
        right_frame = tk.PanedWindow(self.page_frame, orient='vertical', sashwidth=15)

        self.page_frame.add(left_frame , sticky=tk.NSEW, minsize=500)
        self.page_frame.add(right_frame, sticky=tk.NSEW, minsize=500)
        
        self.header_frame = self._create_header_frame(left_frame)
        if self.header_frame is not None:
            #self.header_frame.configure(relief=tk.GROOVE, borderwidth=5)
            left_frame.add(self.header_frame, stretch='first',minsize=150, sticky=tk.NSEW, height=250)

        self.input_frame = self._create_input_frame(left_frame)
        if self.input_frame is not None:
            #self.input_frame.configure(relief=tk.GROOVE, borderwidth=5)
            left_frame.add(self.input_frame, stretch='always',minsize=150, sticky=tk.NSEW, height=200)

        self.start_frame = self._create_start_frame(left_frame)
        if self.start_frame is not None:
            #self.start_frame.configure(relief=tk.GROOVE, borderwidth=5)
            left_frame.add(self.start_frame, stretch='middle',minsize=40, sticky=tk.NSEW)

        self.test_demo_frame = self._create_test_demo_frame(right_frame)
        if self.test_demo_frame is not None:
            #self.test_demo_frame.configure(relief=tk.GROOVE, borderwidth=5)
            right_frame.add(self.test_demo_frame, stretch='first', minsize=150, height=450, sticky=tk.NSEW)

        self.parameter_frame = self._create_parameter_frame(right_frame)
        if self.parameter_frame is not None:
            #self.parameter_frame.configure(relief=tk.GROOVE, borderwidth=5)
            right_frame.add(self.parameter_frame, stretch='last', minsize=150, height=150, sticky=tk.NSEW)

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
            
    def _create_header_frame(self, frame:tk.Frame=None) -> tk.Frame:
        """Creates frame for page header.
                
        Intended to be overridden in subclasses.

        Default creates a frame that displays test name
        """
        if not frame:
            frame = self.root
                    
        header_frame = tk.Frame(frame)
        header_frame.rowconfigure(0, weight=0)
        header_frame.rowconfigure(1, weight=1, minsize=50)
        header_frame.columnconfigure(0, weight=1, minsize=50)
        tk.Label(header_frame, text=self.name, anchor=tk.N).grid(row=0, column=0, sticky=tk.EW)

        text = scrolledtext.ScrolledText(header_frame, wrap=tk.WORD, background=header_frame['bg'])
        text.insert(tk.END, self.description)
        text.configure(state=tk.DISABLED)
        text.grid(row=1,column=0, sticky=tk.NSEW, pady=5, padx=5)


        return header_frame

    def _create_input_frame(self, frame:tk.Frame=None) -> tk.Frame:
        """Creates frame for user inputs.ssddw
        
        Intended to be overridden in subclasses.
        """
        if not frame:
            frame = self.root

        input_frame = tk.Frame(frame)
        self.option_tree = settings.OptionTree(input_frame, self.opts, self.option_sections)
        return input_frame

    def _create_parameter_frame(self, frame:tk.Frame=None) -> tk.Frame:
        return None
    
    def _create_start_frame(self, frame:tk.Frame=None) -> tk.Frame:
        """Creates frame for starting buttons.
        
        Intended to be overridden in subclasses.

        Default creates button that runs start command with no inputs
        """
        if not frame:
            frame = self.root

                    
        header_frame = tk.Frame(frame)
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

    def _create_test_demo_frame(self, frame:tk.Frame=None) -> tk.Frame:
        """Creates frame for test demo plotter.
        
        Intended to be overridden in subclasses.

        Default None
        """
        plotter_frame = tk.LabelFrame(frame, text='Simulated Path', font=("Arial", 14, "bold"), labelanchor=tk.N)
        
        self.plotter = plt.Plotter(plotter_frame, projection='3d')

        if self.robot is not None:
            live_var = tk.BooleanVar(value=False)
            self.plotter.add_menu_option(label='Show Live Robot Posiiton', var=live_var, command=lambda: self.robot.register_live_plotter(self.plotter) if live_var.get() else self.robot.unregister_live_plotter(self.plotter))
        
                
        return plotter_frame

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
        self.opts.add_option(section, 'step_length', 1.0    , tk.DoubleVar(), display_name='Step length', min_value=0.0, max_value=500.0, units='mm' , description='Distance between data recordings.')
        self.opts.add_option(section, 'length'     , 100.0  , tk.DoubleVar(), display_name='Length'     , min_value=0.0, max_value=500.0, units='mm' , description='Length of rectangular path.')
        self.opts.add_option(section, 'height'     , 100.0  , tk.DoubleVar(), display_name='Height'     , min_value=0.0, max_value=500.0, units='mm' , description='Height of rectangular path.')
        self.opts.add_option(section, 'side'       , 'right', tk.StringVar(), display_name='Side'       , values=['left', 'right', 'front'], units=''   , description='Side of the robot that the Gravity Test will perform on.')

        section = 'tests.gravity.variables'
        self.option_sections.append(section)
        self.opts.add_option(section, 'navg'     , 5, tk.IntVar()      , display_name='Sensor Average Readings', units=''  , min_value=1, description='Number of data points recorded at a single point. The average of these points will be returned.')
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold', units='pu', description='Cutoff limit for light intensity readings.')

    def _create_parameter_frame(self, frame = None):
        if frame is None:
            frame = self.root

        paramter_frame = tk.LabelFrame(frame, text='Parameters', labelanchor=tk.N)
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

        return paramter_frame

    def _update_test_demo(self):

        try:
            section = 'tests.gravity.path'
            length = self.opts.get(section, 'length').value
            height = self.opts.get(section, 'height').value
            side   = self.opts.get(section, 'side').value
        except:
            return

        points = LinacTests.create_gravity_test_path_points(self.robot, self.robot.isocenter[:3], length, height, side)
        self.plotter.plot_path('gravity path', points, self.robot.isocenter[:3], label='Gravity Path')
        self.plotter.update()
        
    def start(self):
        try:
            section = 'tests.gravity.path'
            step_length = self.opts.get(section, 'step_length').value
            length      = self.opts.get(section, 'length').value
            height      = self.opts.get(section, 'height').value
            side        = self.opts.get(section, 'side').value

            section = 'tests.gravity.variables'
            threshold = self.opts.get(section, 'threshold').value
            Navg = self.opts.get(section, 'navg').value

        except:
            return

        offset = self.robot.offset.copy()
        self.robot.register_thread()
        try:
            test_results = LinacTests.gravity_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, side, step_length=step_length, length=length, width=height, Navg=Navg)
        finally:
            self.robot.set_widget_statuses(True)
        
        if self.results_page is not None:

            extra_data = {
                'offset': offset,
            }

            inputs = {'step_length': step_length,
                      'length'     : length,
                      'height'     : height,
                      'side'       : side,
                      }
            test_name = f'Gravity_{side}'
            self.results_page.add_test('gravity', test_name, test_results, inputs, **extra_data)

class CollimatorTest(TestPage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom, ls: lq.SensorManager, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        results_page = CollimatorTestResultsPage(_root)
        TestPage.__init__(self, name, _root, robot, ls, opts, description=description, results_page=results_page)
    
    def _default_settings(self):
        section = 'linac.jaws'
        self.opts.add_option(section, 'x1', 10.0  , tk.DoubleVar() , display_name='X1', min_value=0.0, max_value=500.0, units='mm' , description='X1 length of light field at 100 cm')
        self.opts.add_option(section, 'x2', 10.0  , tk.DoubleVar() , display_name='X2', min_value=0.0, max_value=500.0, units='mm' , description='X2 length of light field at 100 cm')
        self.opts.add_option(section, 'y1', 100.0  , tk.DoubleVar(), display_name='Y1', min_value=0.0, max_value=500.0, units='mm' , description='Y1 length of light field at 100 cm')
        self.opts.add_option(section, 'y2', 100.0  , tk.DoubleVar(), display_name='Y2', min_value=0.0, max_value=500.0, units='mm' , description='Y2 length of light field at 100 cm')
        
        section = 'linac.angles'
        self.opts.add_option(section, 'gantry'    , 0.0  , tk.DoubleVar()   , display_name='Gantry angle'    , min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the Gantry')
        self.opts.add_option(section, 'collimator', 0.0  , tk.DoubleVar()   , display_name='Collimator angle', min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the collimator')
        self.opts.add_option(section, 'couch'     , 0.0  , tk.DoubleVar()   , display_name='Couch angle'     , min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the Couch')
        
        section = 'tests.collimator.path'
        self.opts.add_option(section, 'step_length', 1.0  , tk.DoubleVar(), display_name='Step length'  , units='mm' , min_value=0.0, description='Distance between data recordings.')
        self.opts.add_option(section, 'w_umbra'    , 1.0  , tk.DoubleVar() , display_name='Width Umbra' , units='mm' , min_value=0.0, description='Distance past x1/x2 that robot will scan.')
        self.opts.add_option(section, 'l_umbra'    , 0.75 , tk.DoubleVar(), display_name='Length Umbra' , units='mm' , min_value=0.0, description='Distance past y1/y2 that robot will scan.')


        section = 'tests.collimator.variables'
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold', units='pu', description='Cutoff limit for light intensity readings.')
        self.opts.add_option(section, 'navg'     , 5, tk.IntVar()      , display_name='Sensor Average Readings', units=''  , description='Number of data points recorded at a single point. The average of these points will be returned.')
        

        self.option_sections.append('linac')
        self.option_sections.append('tests.collimator')
    
    def _create_parameter_frame(self, frame = None):
        if frame is None:
            frame = self.root

        paramter_frame = tk.LabelFrame(frame, text='Parameters', labelanchor=tk.N)
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
        
        return paramter_frame

    def _update_test_demo(self):

        
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').value
            x2 = self.opts.get(section, 'x2').value
            y1 = self.opts.get(section, 'y1').value
            y2 = self.opts.get(section, 'y2').value
            

            section = 'tests.collimator.path'
            w_umbra = self.opts.get(section, 'w_umbra').value
            l_umbra = self.opts.get(section, 'l_umbra').value

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').value
            collimator_angle = self.opts.get(section, 'collimator').value
            couch_angle = self.opts.get(section, 'couch').value
        except:
            return
        isocenter = self.robot.isocenter[:3]
        points = LinacTests.create_collimator_test_path_points(self.robot, isocenter, x1, x2, y1, y2, w_umbra, l_umbra, gantry_angle, collimator_angle, couch_angle)
        self.plotter.display_light_field(x1, x2, y1, y2, gantry_angle, collimator_angle-couch_angle, isocenter)
        self.plotter.plot_path('Collimator Path', points, isocenter)
        self.plotter._update()

    def start(self):
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').value
            x2 = self.opts.get(section, 'x2').value
            y1 = self.opts.get(section, 'y1').value
            y2 = self.opts.get(section, 'y2').value

            section = 'tests.collimator.path'
            step_length = self.opts.get(section, 'step_length').value
            w_umbra = self.opts.get(section, 'w_umbra').value
            l_umbra = self.opts.get(section, 'l_umbra').value

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').value
            collimator_angle = self.opts.get(section, 'collimator').value
            couch_angle = self.opts.get(section, 'couch').value

            section = 'tests.collimator.variables'
            threshold = self.opts.get(section, 'threshold').value
            Navg = self.opts.get(section, 'navg').value

        except Exception as e:
            logging.critical(f'Could not start Gantry Test:\n{e}')
            raise e

        offset = self.robot.offset.copy()
        self.robot.register_thread()
        try:
            test_results = LinacTests.collimator_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, x1, x2, y1, y2, w_umbra, l_umbra, Navg,
                                                        threshold, step_length, collimator_angle, gantry_angle, couch_angle)
        finally:
            self.robot.set_widget_statuses(True)
        extra_data = {
            'offset': offset,
        }
        
        inputs = {
            'x1'               : x1,
            'x2'               : x2,
            'y1'               : y1,
            'y2'               : y2,
            'step_length'      : step_length,
            'w_umbra'          : w_umbra,
            'l_umbra'          : l_umbra,
            'gantry_angle'     : gantry_angle,
            'collimator_angle' : collimator_angle,
            'couch_angle'      : couch_angle,
            'threshold'        : threshold,
            'Navg'             : Navg,
        }
        if self.results_page is not None:
            
            test_name = f'Collimator_{collimator_angle}Deg'
            self.results_page.add_test('collimator', test_name, test_results, inputs, **extra_data)

class GantryTest(TestPage):
    def __init__(self, name, _root:tk.Frame, robot:rc.RobotCom, ls: lq.SensorManager, opts:settings.OptionDict):
        description = """
        Description
        ___________
        
        Move robotic arm to point the end of the light sensor to the
        approximate location of the isocenter.
        Enter dimensions of the output light field. 

        Press start.
        """
        results_page = CollimatorTestResultsPage(_root)
        TestPage.__init__(self, name, _root, robot, ls, opts, description=description, results_page=results_page)
    
    def _default_settings(self):
        section = 'linac.jaws'
        self.opts.add_option(section, 'x1', 10.0  , tk.DoubleVar() , display_name='X1', min_value=0.0, max_value=500.0, units='mm' , description='X1 length of light field at 100 cm')
        self.opts.add_option(section, 'x2', 10.0  , tk.DoubleVar() , display_name='X2', min_value=0.0, max_value=500.0, units='mm' , description='X2 length of light field at 100 cm')
        self.opts.add_option(section, 'y1', 100.0  , tk.DoubleVar(), display_name='Y1', min_value=0.0, max_value=500.0, units='mm' , description='Y1 length of light field at 100 cm')
        self.opts.add_option(section, 'y2', 100.0  , tk.DoubleVar(), display_name='Y2', min_value=0.0, max_value=500.0, units='mm' , description='Y2 length of light field at 100 cm')
        
        section = 'linac.angles'
        self.opts.add_option(section, 'gantry'    , 0.0  , tk.DoubleVar(), display_name='Gantry angle'    , min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the Gantry')
        self.opts.add_option(section, 'collimator', 0.0  , tk.DoubleVar(), display_name='Collimator angle', min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the collimator')
        self.opts.add_option(section, 'couch'     , 0.0  , tk.DoubleVar(), display_name='Couch angle'     , min_value=-360.0, max_value=360.0, units='deg' , description='Angle set for the Couch')

        section = 'tests.gantry.path'
        self.opts.add_option(section, 'height'     , 100  , tk.DoubleVar(), display_name='Height'      , units='mm' , min_value=0.0, description='Height of the path towards the collimator.')
        self.opts.add_option(section, 'step_length', 1.0  , tk.DoubleVar(), display_name='Step length' , units='mm' , min_value=0.0, description='Distance between data recordings.')
        self.opts.add_option(section, 'w_umbra'    , 1.0 , tk.DoubleVar() , display_name='Width Umbra' , units='mm' , min_value=0.0, description='Distance past x1/x2 that robot will scan.')
        self.opts.add_option(section, 'l_umbra'    , 0.75 , tk.DoubleVar(), display_name='Length Umbra', units='mm' , min_value=0.0, description='Distance past y1/y2 that robot will scan.')

        section = 'tests.gantry.variables'
        self.opts.add_option(section, 'threshold', 0.75, tk.DoubleVar(), display_name='Light Threshold'        , units='pu', min_value=0.0, max_value=1.0, description='Cutoff limit for light intensity readings.')
        self.opts.add_option(section, 'navg'     , 5, tk.IntVar()      , display_name='Sensor Average Readings', units=''  , min_value=1, description='Number of data points recorded at a single point. The average of these points will be returned.')


        self.option_sections.append('linac')
        self.option_sections.append('tests.gantry')

    def _create_parameter_frame(self, frame = None):
        if frame is None:
            frame = self.root

        paramter_frame = tk.LabelFrame(frame, text='Parameters', labelanchor=tk.N)
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

        return paramter_frame

    def _update_test_demo(self):
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').value
            x2 = self.opts.get(section, 'x2').value
            y1 = self.opts.get(section, 'y1').value
            y2 = self.opts.get(section, 'y2').value

            section = 'tests.gantry.path'
            height = self.opts.get(section, 'height').value
            w_umbra = self.opts.get(section, 'w_umbra').value
            l_umbra = self.opts.get(section, 'l_umbra').value

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').value
            collimator_angle = self.opts.get(section, 'collimator').value
            couch_angle = self.opts.get(section, 'couch').value
        except:
            return
        
        isocenter = self.robot.isocenter[:3]
        points = LinacTests.create_gantry_test_path_points(self.robot, isocenter, x1, x2, y1, y2, gantry_angle, collimator_angle, couch_angle, w_umbra, l_umbra, height)
        self.plotter.display_light_field(x1, x2, y1, y2, gantry_angle, collimator_angle, origin=isocenter)
        self.plotter.plot_path('Gantry Path', points, isocenter)
        self.plotter._update()

    def start(self):
        try:
            section = 'linac.jaws'
            x1 = self.opts.get(section, 'x1').value
            x2 = self.opts.get(section, 'x2').value
            y1 = self.opts.get(section, 'y1').value
            y2 = self.opts.get(section, 'y2').value

            section = 'tests.gantry.path'
            height = self.opts.get(section, 'height').value
            step_length = self.opts.get(section, 'step_length').value
            w_umbra = self.opts.get(section, 'w_umbra').value
            l_umbra = self.opts.get(section, 'l_umbra').value

            section = 'linac.angles'
            gantry_angle = self.opts.get(section, 'gantry').value
            collimator_angle = self.opts.get(section, 'collimator').value
            couch_angle = self.opts.get(section, 'couch').value

            section = 'tests.gantry.variables'
            threshold = self.opts.get(section, 'threshold').value
            Navg = self.opts.get(section, 'navg').value

        except Exception as e:
            logging.critical(f'Could not start Gantry Test:\n{e}')
            raise e
        
        self.robot.register_thread()

        offset = self.robot.offset.copy()
        try:
            test_results = LinacTests.gantry_test_automated(self.robot, self.ls, 0.0, 0.0, 0.0, x1, x2, y1, y2, height, w_umbra, l_umbra, 
                                                        threshold, step_length, Navg, collimator_angle, gantry_angle, couch_angle)
        finally:
            self.robot.set_widget_statuses(True)
        
        extra_data = {
            'offset': offset,
        }
        
        inputs = {
                'x1'               : x1,
                'x2'               : x2,
                'y1'               : y1,
                'y2'               : y2,
                'step_length'      : step_length,
                'w_umbra'          : w_umbra,
                'l_umbra'          : l_umbra,
                'gantry_angle'     : gantry_angle,
                'collimator_angle' : collimator_angle,
                'couch_angle'      : couch_angle,
                'threshold'        : threshold,
                'Navg'             : Navg,
            }
        
        test_name = f'Gantry_{gantry_angle}Deg'
        if self.results_page is not None:
            self.results_page.add_test('gantry', test_name, test_results, inputs, **extra_data)
        

INDENT = '\t'

def parse_xrb_file(filename):
    with open(filename, 'rb') as f:
        arr = f.read()

    tests = []
    while arr:
        byte_length, arr = _decode_int(arr)
        test_bytes = arr[:byte_length]
        arr = arr[byte_length:]
        test_type, test_name, current_results, inputs, extra_data = _results_file_read(test_bytes)
        tests.append((test_type, test_name, current_results, inputs, extra_data))

    return tests


# region Test Save

__VERSION__ = '1.1'

def _results_file_text(test_type, test_name, raw_data, inputs, extra_data):
    byte_data = b''
    # Current version
    byte_data += _encode_string(__VERSION__)
    
    # Test info
    byte_data += _encode_string(test_type)
    byte_data += _encode_string(test_name)

    byte_data += extra_data.get('offsets', np.array([0.0]*6)).tobytes()

    # Parse through single level dictionary of inputs
    byte_data += _encode_int(len(inputs))
    for name, value in inputs.items():
        byte_data += _encode_string(name)
        byte_data += _encode_unique_type(value)

    # total number of movements
    byte_data += _encode_int(len(raw_data))
    
    # Create numpy array of data
    for movement_results in raw_data:
        
        positions, distance, intensities = map(list, zip(*movement_results))
        arr = np.column_stack((positions, distance, intensities))
        movement_bytes = b''
        movement_bytes += np.array(list(arr.shape), dtype=np.int64).tobytes()
        movement_bytes += arr.tobytes()
        byte_data += _encode_int(len(movement_bytes)) + movement_bytes
    
    return _encode_int(len(byte_data)) + byte_data

def _results_file_read(arr:bytearray):

    test_version, arr = _decode_string(arr)
    test_type, arr    = _decode_string(arr)
    test_name, arr    = _decode_string(arr)

    extra_data = {}

    if test_version >= '1.1':
        offset_arr = arr[:6*8]
        arr = arr[6*8:]
        offset = np.frombuffer(offset_arr, dtype=np.float64)
        extra_data['offset'] = offset

    inputs = {}
    n_inputs, arr = _decode_int(arr)
    for i in range(n_inputs):
        name, arr  = _decode_string(arr)
        value, arr = _decode_unique_type(arr)
        inputs[name] = value
    
    raw_data = []
    nmovements, arr = _decode_int(arr)
    
    for i in range(nmovements):
        nbytes, arr = _decode_int(arr)
        movement_arr = arr[:nbytes]
        arr = arr[nbytes:]
        
        shape_arr = movement_arr[:16]
        result_data_arr = movement_arr[16:]

        shape = tuple(np.frombuffer(shape_arr, dtype=np.int64))
        restored_1d = np.frombuffer(result_data_arr, dtype=np.float64)
        raw_result_data = restored_1d.reshape(*shape)
        movement_data = [raw_result_data[:, :3], raw_result_data[:,3], raw_result_data[:,4]]
        raw_data.append(tuple(zip(*movement_data)))

    return test_type, test_name, raw_data, inputs, extra_data

def _wrap_test_bytes(test_type, test_name, arr):
    return _encode_string(test_type) + _encode_string(test_name) + _encode_int(len(arr)) + arr

def _encode_string(text:str):
    byte_arr = b''
    byte_arr += _encode_int(len(text))
    byte_arr += text.encode()
    return byte_arr

def _encode_int(value:int):
    return np.array([value], dtype=np.int64).tobytes()

def _encode_unique_type(data: str | int | float | dict):
    b_data = b''
    if isinstance(data, str):
        b_data += _encode_string('s')
        b_data += _encode_string(data)
    elif isinstance(data, int):
        b_data += _encode_string('i')
        b_data += _encode_int(data)
    elif isinstance(data, float):
        b_data += _encode_string('d')
        b_data += struct.pack('d', data)
    elif isinstance(data, dict):
        b_data += _encode_string('D')
        b_data += _encode_int(len(data))
        for name, value in data.items():
            b_data += _encode_string(name)
            b_data += _encode_unique_type(value)
    else:
        raise NotImplementedError(f'Data type {type(data)} for "{data}" not implimented')
    return b_data

def _decode_unique_type(arr):
    _type, arr = _decode_string(arr)
    if _type == 's':
        value, arr = _decode_string(arr)
    elif _type == 'i':
        value, arr = _decode_int(arr)
    elif _type == 'd':
        float_bytes = arr[:8]
        arr = arr[8:]
        value = struct.unpack('d', float_bytes)[0]
    elif _type == 'D':
        n_entries, arr = _decode_int(arr)
        value = {}
        for i in range(n_entries):
            name, arr = _decode_string(arr)
            data, arr = _decode_unique_type(arr)
            value[name] = data
    else:
        raise NotImplementedError(f'Data type {_type} not implimented for decoding')
    return value, arr

def _decode_string(arr:bytearray):
    length, arr = _decode_int(arr)
    return arr[:length].decode(), arr[length:]

def _decode_int(arr:bytearray):
    value = int().from_bytes(arr[0:8], byteorder='little')
    return value, arr[8:]

def save_tests_to_xrb(xrb_file:str, tests):
    with open(xrb_file, 'wb') as f:
                    
        for test_type, test_name, raw_data, inputs, extra_data in tests:
            byte_data = _results_file_text(test_type, test_name, raw_data, inputs, extra_data)
            
            f.write(byte_data)

def save_tests_to_xlsx(xlsx: str, tests):

    if not xlsx or not tests:
        return
    
    with xlsxwriter.Workbook(xlsx) as wb:
        
        for test_type, test_name, raw_data, inputs, extra_data in tests:
            test_name = test_name.strip().replace(' ', '_')
            counter = 0
            sheet_name = test_name
            while sheet_name in wb.sheetnames:
                counter += 1
                sheet_name = f'{test_name}({counter})'
            
            ws = wb.add_worksheet(sheet_name)
            _write_test_page(wb, ws, test_type, test_name, raw_data, inputs)

def _write_test_page(wb:xlsxwriter.Workbook, ws:worksheet.Worksheet, test_type, test_name, raw_data, inputs):


    n_row = 3
    n_col = 0

    chart = wb.add_chart({'type': 'scatter',})

    headers = ['x (mm)', 'y (mm)', 'z (mm)', 'Distance (mm)', 'Light Intensity (lumen)']
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'yellow']
    for i, movement_results in enumerate(raw_data):
        position, distance, intensities = map(list, zip(*movement_results))
        x, y, z = map(list, zip(*position))

        
        ws.merge_range(n_row-2, n_col, n_row-2, n_col+len(headers)-1, f'Movement {i}')
        ws.write_row(n_row-1, n_col, headers)
        

        ws.write_column(n_row, n_col  , x)
        ws.write_column(n_row, n_col+1, y)
        ws.write_column(n_row, n_col+2, z)

        ws.write_column(n_row, n_col+3, distance)
        ws.write_column(n_row, n_col+4, intensities)

        chart.add_series({
                'categories': [ws.name, n_row, n_col+3, n_row+len(intensities)-1, n_col+3],
                'values': [ws.name, n_row, n_col+4, n_row+len(distance)-1, n_col+4],
                'name': f'Movement {i}',
                'color': colors.pop(0) if colors else '',
                'marker': {'type': 'circle'},
                          })

        n_col += len(headers)

    chart.set_x_axis({
        'name': headers[3],
        'major_gridlines': {
            'visible': True, 
            'line': {'width': 1, 'color':'silver'}
        },
    })
    chart.set_y_axis({
        'name': headers[4],
        'major_gridlines': {
            'visible': True, 
            'line': {'width': 1, 'color':'silver'}
        },
    })
    chart.set_legend({
        'position': 'bottom',
    })
    

    ws.merge_range(0, 0, 0, n_col, f'{test_name}')
    ws.insert_chart(n_row, n_col+2, chart)
        
# region OLD

def parse_xrb_file1(filename):
    with open(filename, 'rb') as f:
        arr = f.read()

    tests = []
    while arr:
        test_type, arr = _decode_string(arr)
        test_name, arr = _decode_string(arr)
        byte_length, arr = _decode_int(arr)
        test_bytes = arr[:byte_length]
        arr = arr[byte_length:]

        if test_type == 'gravity':
            current_results, inputs = _gravity_test_results_file_read(test_bytes)
        elif test_type == 'collimator':
            current_results, inputs = _collimator_test_results_file_read(test_bytes)
        else:
            raise ValueError(f'Test type {test_type} not supported!')
        
        tests.append((test_type, test_name, current_results, inputs))

    return tests

def _gravity_test_results_file_text(test_name, result_data, inputs):
    
    byte_data = b''
    byte_data += _encode_string(test_name)
    byte_data += _encode_string(side)

    byte_data += _encode_int(len(result_data))
    
    # Create numpy array of data
    for movement_results in result_data:
        
        positions, distance, intensities = map(list, zip(*movement_results))
        arr = np.column_stack((positions, distance, intensities))
        movement_bytes = b''
        movement_bytes += np.array(list(arr.shape), dtype=np.int64).tobytes()
        movement_bytes += arr.tobytes()
        byte_data += _encode_int(len(movement_bytes)) + movement_bytes
    
    return _wrap_test_bytes('gravity', test_name, byte_data)

def _gravity_test_results_file_read(arr:bytearray):
    test_name, arr = _decode_string(arr)
    side, arr = _decode_string(arr)

    result_data = []
    nmovements, arr = _decode_int(arr)
    
    for i in range(nmovements):
        nbytes, arr = _decode_int(arr)
        movement_arr = arr[:nbytes]
        arr = arr[nbytes:]
        
        shape_arr = movement_arr[:16]
        result_data_arr = movement_arr[16:]

        shape = tuple(np.frombuffer(shape_arr, dtype=np.int64))
        restored_1d = np.frombuffer(result_data_arr, dtype=np.float64)
        raw_result_data = restored_1d.reshape(*shape)
        movement_data = [raw_result_data[:, :3], raw_result_data[:,3], raw_result_data[:,4]]
        result_data.append(tuple(zip(*movement_data)))

    return result_data, {}

def _collimator_test_results_file_text(test_type, test_name, raw_data, inputs):
    
    byte_data = b''
    byte_data += _encode_string(test_name)

    byte_data += _encode_int(len(raw_data))
    
    # Create numpy array of data
    for movement_results in raw_data:
        
        positions, distance, intensities = map(list, zip(*movement_results))
        arr = np.column_stack((positions, distance, intensities))
        movement_bytes = b''
        movement_bytes += np.array(list(arr.shape), dtype=np.int64).tobytes()
        movement_bytes += arr.tobytes()
        byte_data += _encode_int(len(movement_bytes)) + movement_bytes
    
    return _wrap_test_bytes('collimator', test_name, byte_data)

def _collimator_test_results_file_read(arr:bytearray):
    test_name, arr = _decode_string(arr)

    result_data = []
    nmovements, arr = _decode_int(arr)
    
    for i in range(nmovements):
        nbytes, arr = _decode_int(arr)
        movement_arr = arr[:nbytes]
        arr = arr[nbytes:]
        
        shape_arr = movement_arr[:16]
        result_data_arr = movement_arr[16:]

        shape = tuple(np.frombuffer(shape_arr, dtype=np.int64))
        restored_1d = np.frombuffer(result_data_arr, dtype=np.float64)
        raw_result_data = restored_1d.reshape(*shape)
        movement_data = [raw_result_data[:, :3], raw_result_data[:,3], raw_result_data[:,4]]
        result_data.append(tuple(zip(*movement_data)))

    return result_data, {}


def alan_function(filename, index):
    tests = list(parse_xrb_file(filename))
    test_type, test_name, test_results, inputs = tests[index]
    print(f'Picking {test_type} test: "{test_name}"')
    if test_type == 'gravity':
        current_results = _gravity_test_results_file_read(test_results)
    else:
        raise ValueError(f'Test type {test_type} not supported!')
    
    return current_results

#test_results = alan_function(r'TestData/Official Gravity/GravityTest1.xrb', 0)
#for pos, distance, intensity in test_results[2]:
#    print(pos, distance, intensity)