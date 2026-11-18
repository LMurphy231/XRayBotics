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
import XRBPlotter as plt
import settingshandler as settings
import TestPages as tp

import PackageInstaller
PackageInstaller.install_required()

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
class GUILogHandler(logging.Handler):
    def __init__(self, level):
        self.log_text: list[tuple[float, int, str]] = []
        self.texts: list[tk.Text] = []
        super().__init__(level)

    def clear(self):
        self.log_text.clear()

    def get(self):
        return self.log_text.copy()
    
    def register_text(self, text:tk.Text):
        if text not in self.texts:
            self.texts.append(text)

    def unregister_text(self, text:tk.Text=None):
        if text is None:
            self.texts.clear()

        elif text in self.texts:
            self.texts.remove(text)

    def emit(self, record:logging.LogRecord):
        try:
            msg = self.format(record)
            self.log_text.append((time.time(), record.levelno, msg))
            try:
                for text in self.texts:
                    _write_to_textbox(text, msg)
            except:
                return

        except Exception:
            self.handleError(record)

class GUI:
    def __init__(self, name = 'XRayBotics'):
        self._root = tk.Tk()
        self.name = name
        self._root.title(name)
        self.settings_window = None
        _create_styles(self._root)

        # Load options
        self.opts = settings.OptionDict(INI)
        self._default_options()

        self.robot = rc.RobotCom(self.opts)
        self.ls = ls.SensorManager()
        
        self._create_loggers()
        self.build()

        self._root.protocol('WM_DELETE_WINDOW', self._on_close)
        self._root.mainloop()
        self.ls.close()

    def _on_close(self):
        self.ls.close()
        self._root.destroy()

    def build(self):

        self._create_menu()

        # Allow the 
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_rowconfigure(0, weight=1)


        self.window_pane = tk.PanedWindow(self._root, orient=tk.HORIZONTAL, sashwidth=15)
        self.window_pane.grid(row=0, column=0, sticky=tk.NSEW)

        self.root = tk.Frame(self.window_pane)
        self.window_pane.add(self.root, minsize=600)

        self.page_frame = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashwidth=15)
        self.page_frame.pack(expand=True, fill=tk.BOTH)
        
        
        test_setup_frame = tk.Frame(self.page_frame)
         
        self._create_test_setup(test_setup_frame)
        self.page_frame.add(test_setup_frame, sticky=tk.NSEW, minsize=300)

        robot_window_frame = tk.LabelFrame(self.page_frame, text='Robot Controller')
        
        self._create_robot_controller(robot_window_frame)
        self.page_frame.add(robot_window_frame, sticky=tk.NSEW, minsize=150)

        self.text_window_frame = tk.Frame(self.window_pane)
        self._create_text_window(self.text_window_frame)

        
        self.settings_frame = tk.Frame(self._root)
    
    def _create_loggers(self):
        self.movement_handlers: dict[str, GUILogHandler] = {}
        for logger_name in ('Automated Tests', 'Moving', 'Scanning', 'Data Storage', 'Path Movement', 'Robot Communication', 'Joint Positions'):
            handler = GUILogHandler(logging.DEBUG)
            handler.setFormatter(logging.Formatter('[%(levelname)-8s][%(asctime)s] - %(message)s', datefmt='%H:%M:%S'))
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False

            logger.addHandler(handler)
            self.movement_handlers[logger_name] = handler

    def _create_menu(self):
        self.menubar = tk.Menu(self._root, tearoff=False)

        # Settings Menu
        settings_menu = tk.Menu(self.menubar, tearoff=False)
        settings_menu.add_command(label="All", command=lambda: self._create_option_window(self.settings_frame, '').grid(row=0, column=0, pady=1,sticky=tk.NSEW))
        settings_menu.add_command(label="Robot", command=lambda: self._create_option_window(self.settings_frame, ['robot',]).grid(row=0, column=0, pady=1,sticky=tk.NSEW))

        # View Menu
        def add_text_window():
            # Lock the current size of the window pane
            frame_width = self.window_pane.winfo_width()
            frame_height = self.window_pane.winfo_height()
            self.window_pane.configure(width=frame_width, height=frame_height)

            # Add text window to panes
            target_width = 250
            self.window_pane.add(self.text_window_frame, minsize=target_width, height=target_width, sticky=tk.NSEW)
            
        communications_menu = tk.Menu(self.menubar, tearoff=False)
        communications_menu.add_command(label="Messages", command=add_text_window)

        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        self.menubar.add_cascade(label="View", menu=communications_menu)

        self._root.config(menu=self.menubar)

    def _create_robot_controller(self, frame:tk.Frame):
        self.robot_vars = {}
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        robot_frame = tk.PanedWindow(frame, sashwidth=10, orient=tk.HORIZONTAL)
        robot_frame.grid(sticky=tk.NSEW)

        left_pane = tk.Frame(robot_frame)
        plotter_frame = tk.LabelFrame(robot_frame, text='Robot Viewer', font=("Arial", 14, "bold"), labelanchor=tk.N)

        robot_frame.add(left_pane, minsize=100)
        robot_frame.add(plotter_frame, minsize=100)
        
        move_type_notebook = ttk.Notebook(left_pane)
        move_type_notebook.grid(row=0, column=0, sticky=tk.NSEW)

        button_frame = tk.Frame(left_pane)
        button_frame.grid(row=0, column=1, sticky=tk.NSEW)

        self.robot_plotter = plt.Plotter(plotter_frame, '3d')
        self.robot_plotter._set_axis_limit(-500,500,-500,500,-500,500)
        self.robot.register_live_plotter(self.robot_plotter)

        estimated_name = 'Estimated Next Position'
        estimated_color = 'orange'


        movement_options  = {
            'Coordinate Movement' : {
                'var_names' : ['x', 'y', 'z', 'rx', 'ry', 'rz'],
                'plot_function' : lambda position_vars: self.robot.plot_new_position(self.robot._get_movement_pos(*[var.get() for var in position_vars]), self.robot_plotter, name=estimated_name, color=estimated_color, is_joint=False),
                'move_function' : lambda position_vars: self.robot.move_position(*[var.get() for var in position_vars], in_thread=True),
                'limits': [(-500.0, 500.0),]*3+[(-180, 180),]*3,
            },
            'Incremental Movement' : {
                'var_names' : ['dx', 'dy', 'dz', 'drx', 'dry', 'drz'],
                'plot_function' : lambda position_vars: self.robot.plot_new_position(self.robot._get_movement_pos(*[var.get() for var in position_vars]), self.robot_plotter, name=estimated_name, color=estimated_color, is_joint=False),
                'move_function' : lambda position_vars: self.robot.move_increment(*[var.get() for var in position_vars], in_thread=True),
                'limits': [(-250.0, 250.0),]*3+[(-180, 180),]*3,
            },
            'Joint Movement' : {
                'var_names' : ['Joint 1', 'Joint 2', 'Joint 3', 'Joint 4', 'Joint 5', 'Joint 6'],
                'plot_function' : lambda position_vars: self.robot.plot_new_position([var.get() for var in position_vars], self.robot_plotter, name=estimated_name, color=estimated_color, is_joint=True),
                'default': self.robot.HOME,
                'move_function' : lambda position_vars: self.robot.move_joint([var.get() for var in position_vars], in_thread=True),
                'limits': self.robot.AXIS_LIMIT,
            },
        }
        function_changes = {}
        for movement_type, obj in movement_options.items():
            sub_frame = tk.Frame(move_type_notebook)
            minior_frames = (tk.Frame(sub_frame), tk.Frame(sub_frame))
            minior_frames[0].grid(row=0, column=0, sticky=tk.NSEW)
            bool_var = tk.BooleanVar(value=False)
            tk.Checkbutton(sub_frame, text='Use Slider', variable=bool_var, command=lambda *args, frames=minior_frames, var=bool_var: 
                    (frames[0 if var.get() else 1].grid_forget(),
                    frames[1 if var.get() else 0].grid(row=0, column=0, sticky=tk.NSEW),),
                    ).grid(row=1, column=0)
            
            move_type_notebook.add(sub_frame, text=movement_type)
            default_values = obj.get('default', [0.0]*len(obj['var_names']))
            movement_vars = []
           
            for index, var_name in enumerate(obj['var_names']):
                
                
                var = tk.DoubleVar(value=default_values[index])
                movement_vars.append(var)

                for i, minor_frame in enumerate(minior_frames):
                    tk.Label(minor_frame, text=f'{var_name}:').grid(row=index%3, column=2*(index//3),sticky=tk.NSEW)
                    if i == 0:  
                        widget = tk.Entry(minor_frame, textvariable=var)
                    else:
                        widget = tk.Frame(minor_frame)
                        tk.Label(widget, textvariable=var, width=5).grid(row=0, column=0,sticky=tk.EW)
                        from_, to = obj['limits'][i]
                        tk.Scale(widget, from_=from_, to=to, orient=tk.HORIZONTAL, width=13, resolution=0.01, variable=var, showvalue=False, ).grid(row=0, column=1, sticky=tk.NSEW)#command=lambda *args, vars=movement_vars, obj=obj: obj['plot_function'](vars)
                    
                    widget.grid(row=index%3,column=1+2*(index//3),sticky=tk.NSEW)
                    minor_frame.columnconfigure(1+2*(index//3), minsize=75)
                

            for var in movement_vars:
                var.trace_add('write', lambda *args, obj=obj, vars=movement_vars: obj['plot_function'](vars))

            function_changes[movement_type] = (
                lambda *args, vars=movement_vars, obj=obj: obj['move_function'](vars),
                lambda *args, vars=movement_vars, defaults=default_values: [_reset_var(default, var) for default, var in zip(defaults, vars)],
                )



        movement_frame = tk.LabelFrame(button_frame, text='Movement Commands')
        movement_frame.grid(sticky=tk.NSEW)

        move_to_frame = tk.LabelFrame(button_frame, text='Move to Position')
        move_to_frame.grid(sticky=tk.NSEW)

        var_frame = tk.LabelFrame(button_frame, text='Other')
        var_frame.grid(sticky=tk.NSEW)
        
        button_options = {
            'width': 10, 
        } 
        button_grid_cnf = {
            'sticky': tk.NSEW,
            'padx':2,
            'pady':2,
        }
        move_button = tk.Button(movement_frame, text='Move', cnf=button_options)
        stop_button = tk.Button(movement_frame, text='Stop Robot'   , command = self.robot.interrupt_threads, cnf=button_options)
        stop_button.grid(row=0, column=1, cnf=button_grid_cnf)
        move_button.grid(row=0, column=0, cnf=button_grid_cnf)

        clear_button = tk.Button(movement_frame, text='Clear Error'  , command = lambda: print(self.robot.ResetAllError()),cnf=button_options)
        set_isocenter_button = tk.Button(movement_frame, text='Set Isocenter', command = lambda: self.robot.set_isocenter(self.robot._get_tool_position()),cnf=button_options)
        set_isocenter_button.grid(row=1, column=0, cnf=button_grid_cnf)
        clear_button.grid(row=1, column=1, cnf=button_grid_cnf)
        

        isocenter_button = tk.Button(move_to_frame, text='Isocenter'  , command = self.robot.move_to_isocenter,cnf=button_options)
        home_button = tk.Button(move_to_frame, text='Home', command = lambda: self.robot.move_to_home(),cnf=button_options)
        isocenter_button.grid(row=0, column=0, cnf=button_grid_cnf)
        home_button.grid(row=0, column=1, cnf=button_grid_cnf)

        reset_var_button = tk.Button(var_frame, text='Reset', cnf=button_options)
        reset_var_button.grid(row=0, column=0, cnf=button_grid_cnf)

        self.robot._disable_move_widgets.extend([move_button, home_button, set_isocenter_button, isocenter_button])

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

    def _create_test_setup(self, frame:tk.Frame):
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        self.test_frame = tk.Frame(frame)
        self.test_frame.grid(row=0, column=1, sticky=tk.NSEW)
        
        self.test_frame.grid_columnconfigure(0, weight=1)
        self.test_frame.grid_rowconfigure(0, weight=1)
        
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

        # Allow frame to adjust size
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        tk.Button(frame, text='Close', command=lambda: self.window_pane.remove(frame)).grid(row=0, column=1, sticky=tk.NE)

        self.logger_selection = tk.StringVar(value='All')
        self.level_selection  = tk.StringVar(value='Debug')
        self.logging_levels = {
            'Debug'   : logging.DEBUG,
            'Info'    : logging.INFO,
            'Warning' : logging.WARNING,
            'Error'   : logging.ERROR,
            'Critical': logging.CRITICAL,

        }
        funct = lambda event=None: self._display_log(self.logging_textbox, [option for option, var in type_vars.items() if var.get()], self.logging_levels[self.level_selection.get()])
        available_loggers = ['All',] + list(self.movement_handlers.keys())

        # Create a frame for the logger type manu
        menu_frame = tk.Frame(frame)
        menu_frame.grid(row=1, column=0, sticky=tk.EW)
        menu_frame.columnconfigure(0, weight=1)

        type_menu = tk.Menubutton(menu_frame, text='Loggers')
        type_menu.grid(row=0, column=0, sticky=tk.EW)

        menu = tk.Menu(type_menu, tearoff=False)
        type_menu['menu'] = menu
        
        def menu_click(vars, menu:tk.Widget, parent, is_all):
            """Toggles 'All" variable. Replaces menu at the bottom left corner of the parent frame."""
            if is_all:
                for var in vars.values():
                    var.set(vars['All'].get() )

            vars['All'].set(all([var.get() for name, var in vars.items() if name != 'All']))

            # Replace menu at the bottom left corner of the parent frame
            menu.post(parent.winfo_rootx(), parent.winfo_rooty() + parent.winfo_height())
            
        type_vars = {}
        for option in available_loggers:
            var = tk.BooleanVar(value=True)
            type_vars[option] = var
            menu.add_checkbutton(label=option, variable=var, command=lambda type_vars=type_vars, menu=menu, option=option: (menu_click(type_vars, menu, menu_frame, option == 'All'), funct()))

        ttk.OptionMenu(frame, self.level_selection , 'Info', *list(self.logging_levels.keys()), command=lambda event=None: funct()).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        message_frame = tk.Frame(frame)
        message_frame.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW)
        
        self.logging_textbox = scrolledtext.ScrolledText(message_frame, wrap=None, state=tk.NORMAL)
        self.logging_textbox.pack(expand=True, fill=tk.BOTH)
        funct()

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

    def _default_options(self):
        return

    def _display_log(self, text: tk.Text, logger_names: list[str], level=logging.DEBUG):
        all_text = []
        for logger_name, handler in self.movement_handlers.items():
            if 'All' in logger_names or logger_name in logger_names:
                handler.register_text(text)
            else:
                handler.unregister_text(text)
                continue

            all_text.extend(handler.get())
            
        all_text = sorted(all_text, key=lambda x: x[0])

        text.config(state=tk.NORMAL)
        text.delete('1.0', tk.END)
        _write_to_textbox(text, '\n'.join([item[-1] for item in all_text if item[1] >= level]))

def verify_vars(funct:object, vars):
    pass

    
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

if __name__ == '__main__':
    GUI()