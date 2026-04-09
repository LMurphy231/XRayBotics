import os, glob, inspect
import typing
from collections import UserDict
import dataclasses
import time

from tkinter import *
from tkinter import ttk, filedialog, colorchooser
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.font_manager import FontProperties
import f3d
from pyopengltk import OpenGLFrame
import matplotlib.axes as axes

import numpy
 
SCATTER_MARKERS = [('Point', '.'        ),('Pixel', ','        ),('Circle', 'o'       ),
                   ('Triangle Up', '^'  ),('Triangle Down', 'v'),('Triangle Left', '<'),('Triangle Right', '>'),
                   ('Tri Up', '1'       ),('Tri Down', '2'     ),('Tri Left', '3'     ),('Tri Right', '4'),
                   ('Octogon', '8'      ),('Square', 's'       ),('Pentagon', 'p'     ),('Star', '*'),
                   ('Plus (filled)', 'P'),('Plus', '+'         ),('Hexagon 1', 'h'    ),('Hexagon 2', 'H'),
                   ('X', 'x'            ),('X (filled)', 'X'   ),('Diamond', 'D'      ),('Thin Diamond', 'd'),
                   ('vline', '|'        ),('hline', '_'        ),
                   ('Tick Left', 0      ),('Tick Right', 1     ),('Tick Up', 2        ),('Tick Down', 3),
                   ('Care Left', 4      ),('Care Right', 5     ),('Care Up', 6        ),('Care Down', 7),
                   ('Care Left Base', 8 ),('Care Right Base', 9),('Care Up Base', 10  ),('Care Down Base', 11),]
 
def _is_tk_kwarg(tk_class, **kwargs):
    if tk_class == Pack:
        pack_keys = ['after', 'anchor', 'before', 'expand', 'fill', 'in', 'ipadx', 'ipady', 'padx', 'pady', 'side']
        return {kw: kwargs[kw] for kw in kwargs if kw in pack_keys}
    if tk_class == Grid:
        pack_keys = ['column', 'columnspan', 'in', 'in_', 'ipadx', 'ipady', 'padx', 'pady', 'row', 'rowspan', 'sticky']
        return {kw: kwargs[kw] for kw in kwargs if kw in pack_keys}
    return {kw: kwargs[kw] for kw in kwargs if kw in tk_class().keys()}
   
def _is_child(widget, parent):
    if widget in parent.winfo_children():
        return True
    for child in parent.winfo_children():
        is_child = _is_child(widget, child)
        if is_child:
            return True
    return False
 
def _is_attribute(item, key_phrase=None, dict_=None, **kwargs):
    if key_phrase is not None:
        return {key: kwargs[key] for key in kwargs if getattr(item,key_phrase.format(key),None) is not None}
    if dict_ is not None:
        return {key: kwargs[key] for key in kwargs if key in dict_}
    return {key: kwargs[key] for key in kwargs if key in str(inspect.signature(item))}
 
def _get_scatter_type(marker, value=False):
    if value:
        for name, marker_value in SCATTER_MARKERS:
            check_val  = name if value else marker_value
            return_val = name if not value else marker_value
            if check_val == marker:
                return return_val
    return marker
 
def create_slider(widget, frame, axis='both', **options):
    default_options={}
    default_options.setdefault('x', add_kwarg(orient=HORIZONTAL, command=widget.xview, jump=True, side=BOTTOM, expand=True , fill=X))
    default_options.setdefault('y', add_kwarg(orient=VERTICAL  , command=widget.yview, jump=True, side=RIGHT , expand=False, fill=BOTH))
    options = _combine_options(options, default_options)
    if axis=='both' or axis=='x':
        xslider = Scrollbar(frame, **_is_tk_kwarg(Scrollbar, **options['x']))
        xslider.pack(**_is_tk_kwarg(Pack, **options['x']))
        widget.configure(xscrollcommand = xslider.set)
        if axis == 'x':
            return xslider
    if axis=='both' or axis=='y':
        yslider = Scrollbar(frame, **_is_tk_kwarg(Scrollbar, **options['y']))
        yslider.pack(**_is_tk_kwarg(Pack, **options['y']))
        widget.configure(yscrollcommand = yslider.set)
        if axis == 'y':
            return yslider
    return xslider, yslider
 
def create_widget(root, name, widget_type='combobox', return_type=str, get_widgets=(), **options):
    default_options={}
    default_options.setdefault('label_frame'        , add_kwarg(borderwidth=0, side=TOP, fill=X, expand=True, relief=FLAT))
    default_options.setdefault('frame'              , None)
    default_options.setdefault('combobox'           , add_kwarg(values=[], height=15, state='readonly', side=LEFT, fill=X, expand=True, anchor=CENTER))
    default_options.setdefault('checkbutton'        , add_kwarg(style='TCheckbutton', side=TOP, fill=X, anchor=CENTER))
    default_options.setdefault('entry'              , add_kwarg(height=5, side=LEFT, fill=X, expand=False, anchor=CENTER, pady=5))
    default_options.setdefault('color'              , add_kwarg(height=25, width=25, side=LEFT, bg='white'))
    default_options.setdefault('bind'               , None )
    default_options.setdefault('on_empty'           , [])
    widgets = {}
    options = _combine_options(options, default_options)
 
    if options['label_frame'] is not None and options['frame'] is None:
        frame = LabelFrame(root, **_is_tk_kwarg(LabelFrame, **options['label_frame']))
        frame.pack(**_is_tk_kwarg(Pack, **options['label_frame']))
    elif options['frame'] is not None:
        frame = Frame(root, **_is_tk_kwarg(Frame, **options['frame']))
    else:
        frame = root
    widgets['label_frame'] = widgets['frame'] = frame
    if widget_type   =='combobox':
        slct_widget  = ttk.Combobox(frame,    **_is_tk_kwarg(ttk.Combobox,    **options[widget_type]))
    elif widget_type == 'entry':
        slct_widget  = ttk.Entry(frame,       **_is_tk_kwarg(ttk.Entry,       **options[widget_type]))
    elif widget_type == 'scale':
        slct_widget  = ttk.Scale(frame,       **_is_tk_kwarg(ttk.Scale,       **options[widget_type]))
    elif widget_type == 'checkbox':
        slct_widget  = ttk.Checkbutton(frame, **_is_tk_kwarg(ttk.Checkbutton, **options[widget_type]))
    elif widget_type == 'color':
        slct_widget  = ColorWidget(frame,     **_is_tk_kwarg(Canvas,          **options[widget_type]))
 
    widgets[widget_type] = slct_widget
    slct_widget.pack(**_is_tk_kwarg(Pack, **options[widget_type]))
    binding=None
    if options['bind'] is not None:
        bind = options['bind']
        binding = slct_widget.bind(bind['bind'], lambda e, callback_func=bind['function']: callback_func())
    var_type = 'var'          if 'var'          in options[widget_type] else None
    var_type = 'textvariable' if 'textvariable' in options[widget_type] else var_type
    var_type = 'variable'     if 'variable'     in options[widget_type] else var_type
    var      = slct_widget    if var_type       is None                 else options[widget_type][var_type]
    widgets['var'] = var
    widgets['linked_var'] = LinkedVar(name, var, frame, slct_widget, return_type, bind=binding,
                                        on_empty=options['on_empty'])
    return_widgets = [widgets['linked_var']]
    if isinstance(get_widgets, str):
        if get_widgets in widgets:
            return_widgets.append(widgets[get_widgets])
    else:
        for widget in get_widgets:
            if widget in widgets:
                return_widgets.append(widgets[widget])
    return tuple(return_widgets) if len(return_widgets)>1 else return_widgets[0]

def create_frame(root: typing.Union[Frame, LabelFrame], start_row, start_col, rowspan=1, colspan=1, frame_type=Frame, cnf={}, **options) -> typing.Union[Frame, LabelFrame]:
    options = _combine_options(options, cnf)
    for i in range(start_row, start_row+rowspan):
        root.grid_rowconfigure(i, weight=1)
    for i in range(start_col, start_col+colspan):
        root.grid_columnconfigure(i, weight=1)
    frame = frame_type(root, **_is_tk_kwarg(frame_type, **options))
    frame.grid(row=start_row, column=start_col, rowspan=rowspan, columnspan=colspan, **_is_tk_kwarg(Grid, **options))
    return frame

def create_var(set=None, function=None, var=None):
    var = var if var is not None else StringVar()
    if set is not None:
        var.set(set)
    if function is not None:
        var.trace_add('write', function)
    return var
 
def _scroll(canvas, event, vars={}):
    if not _is_child(event.widget, canvas):
        return
   
    for var in vars.values():
        if type(var.widget) == ttk.Combobox:
            try:
                # Check if Combobox popdown is open
                if var.widget.tk.call('winfo', 'viewable', var.widget.tk.call('ttk::combobox::PopdownWindow', var.widget)):
                    return
            except:
                pass
   
    # Prevent scrolling when entire canvas is shown
    if canvas.yview() == (0.0, 1.0):
        event.delta = 0
    canvas.yview_scroll(-1*int(event.delta/120), 'units')
    canvas.configure(scrollregion=canvas.bbox(ALL))
 
def precision(value, prec):
    try:
        value = float(value)
    except:
        return value
    tens = len(str(value).split('.')[0]) - 1
    return float(f'{value:0.{tens+prec}e}')
 
def add_kwarg(**kwarg):
    return kwarg
 
def no_function(*args):
    pass
 
def _combine_options(options, default_options):
    for key in default_options:
        if key not in options:
            options[key] = default_options[key]
            continue
        if not isinstance(options[key],dict) or default_options[key] is None or options[key] is None:
            continue
        for option in default_options[key]:
            if option not in options[key]:
                options[key][option] = default_options[key][option]
    return options
 
def _get_user_file(single=False, file_types = [("All Files", "*.*")]):
    all_file_types = ('All Files', tuple(file_type for _, file_type in file_types))
    if ("All Files", "*.*") in file_types:
        del file_types[file_types.index(("All Files", "*.*"))]
    if single:
        return filedialog.askopenfilename(
        title="Open File",
        initialdir=os.path.dirname(__file__),  # Optional: Set initial directory
        filetypes=(all_file_types, *file_types)# Optional: Filter file types
    )
    return filedialog.askopenfilenames(
        title="Open File(s)",
        initialdir=os.path.dirname(__file__),  # Optional: Set initial directory
        filetypes=(all_file_types, *file_types)# Optional: Filter file types
    )
 
def _radius(x1,y1,z1,x2,y2,z2):
    return numpy.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
 
def _angle(x1,y1,z1,x2,y2,z2):
    r = _radius(x1,y1,z1,x2,y2,z2)
    theta = numpy.atan2(y1-y2, x1-x2)
    phi = numpy.arccos((z1-z2)/r)
    return phi, theta
 
class ColorWidget():
    def __init__(self, root, **options):
        self.widget = Canvas(root, _is_tk_kwarg(Canvas, **options))
       
    def pack(self, **options):
        self.widget.pack(**_is_tk_kwarg(Pack, **options))
   
    def get(self):
        return self.widget['background']
 
    def set(self, value, **options):
        options['bg']=value
        self.widget.configure(**_is_tk_kwarg(Canvas, **options))
 
    def configure(self, values=None, **options):
        self.widget.configure(**_is_tk_kwarg(Canvas, **options))
   
    def state(self, state=None):
        if state is not None:
            self.widget['state'] = state
        return self.widget['state']
 
class LinkedVar():
    def __init__(self, name, var, frame, widget, out_type, **options):
        options.setdefault('float_precision', 6)
        options.setdefault('bind', None)
        options.setdefault('on_empty', [])
        self.options     = options
        self.name        = name
        self.var         = var
        self.widget      = widget
        self.value       = self.var.get()
        self.type        = type(var)
        self.frame       = frame
        self.out_type    = out_type
        self.state       = widget.state()
        self.all_widgets = {'frame': self.frame, 'widget': self.widget}
        self.pack_data   = {}
        for widget in self.all_widgets:
            self.pack_data[widget] = {}
            self._pack_info(widget)
       
    def get(self):
        try:
            # Use combobox widget to get data
            if self.type == ttk.Combobox:
                entry = self.widget.get()
            # Use var to get data
            else:
                entry = self.var.get()
            # Convert entry to out data type
            entry = 0 if (self.out_type == int or self.out_type == float) and not entry else entry
            self.value = self.out_type(entry)
        except:
            print(f'{self.name} FAILED: {self.value}')
        return self.value
       
    def get_all(self):
        return self.widget['values']
   
    def toggle_bind(self, state=True):
        if self.widget is None or self.options['bind'] is None:
            return
        # Bind Widget
        if state:
            self.widget.bind(self.options['bind'])
        # Unbind Widget
        else:
            try:
                self.widget.unbind(self.options['bind'])
            except:
                pass
   
    def verify_state(self, state=True):
        if self.state is None or not state:
            return
        self.widget.configure(state = self.state)
 
    def _pack_info(self, widget_type):
        if widget_type not in self.all_widgets:
            return {}
        current_pack_info = self._get_pack(self.all_widgets[widget_type])
        self.pack_data[widget_type] = current_pack_info if current_pack_info != {} else self.pack_data[widget_type]
        return self.pack_data[widget_type]
   
    def _get_pack(self, widget):
        try:
            return widget.pack_info()
        except:
            return {}
   
    def _is_empty(self):
        self._empty_disable()
        self._empty_hide()
        return True if self.get() else False
   
    def _empty_hide(self):
        if 'hide' in self.options['on_empty']:
            self.show(True if self.get() else False)
   
    def _empty_disable(self):
         if 'disable' in self.options['on_empty']:
            self.enable(True if self.get() else False)
 
    def show(self, state=True):
        if state:
            self.frame.pack(**self._pack_info('frame'))
        else:
            self.frame.pack_forget()
 
    def enable(self, state=True):
        for widget in self.frame.winfo_children():
            widget['state'] = (self.state if widget is self.widget else NORMAL) if state else DISABLED
 
    def set_value(self, value):
        # Verify that widget is enabled
        self.verify_state()
        value = value if value is not None else ''
        try:
            self.var.set(self.out_type(precision(value, self.options['float_precision'])))
        except:
            self.widget_change(set_value=precision(value, self.options['float_precision']))
        self._is_empty()
 
    def widget_change(self, add=None, remove=None, values=None, set_value=None):
        self.verify_state()
        # Return if there is no widget
        if self.widget is None:
            return
       
        # Get all values or use given values
        if values is not None:
            values = [values] if not isinstance(values, list) else values
        else:
            try:
                values = list(self.widget['values'])
            except:
                return
        #Add New Values
        if add is not None:
            add = [add] if not isinstance(add, list) else add
            for new_value in add:
                if new_value not in values:
                    values.append(new_value)
        #Remove Values
        if remove is not None:
            remove = [remove] if not isinstance(remove, list) else remove
            for old_value in remove:
                if old_value in values:
                    values.pop(values.index(old_value))
        #Update Widget Values
        if values is not None:
            self.widget.configure(values=values)
 
        #Set Widget Value
        if set_value is not None:
            self.set_value(set_value)
        self._is_empty()
        return values

class ConnectionStatus:
    def __init__(self, root: typing.Union[Label, LabelFrame], row, col, rowspan=1, colspan=1, bars = 3, status=0.0, **options):
        self.root = create_frame(root,row, col, rowspan, colspan, LabelFrame, options, text='Connection Status')
        self.bars: list[Frame] = [] 
        minsize=10
        for i in range(bars):
            self.root.columnconfigure(i, weight=1, minsize=2)
            #self.root.rowconfigure(i, weight=1, minsize=minsize)
            self.root.rowconfigure(2*bars-i, weight=1, minsize=minsize)
            self.bars.append(create_frame(self.root, 2*bars-i, i, 1+i*2, 1, Frame, relief=GROOVE, bg='green', sticky=NSEW, borderwidth=1, padx=max(1, 5-bars)))
        
        self._update(status)

    def _update(self, status=0.0):
        self.status = float(status)
        if self.status <= 0.0:
            color = "#3B3B3B"
        elif 0.0 < self.status <= 0.25:
            color = "#FF0000"
        elif 0.25 < self.status <= 0.75:
            color = "#FFF000"
        else:
            color = "#008F15"
        
        for i, bar in enumerate(self.bars):
            if int(self.status*len(self.bars)) >= i:
                bar.configure(bg = color if i != len(self.bars)-1 or color == "#008F15" else "#3B3B3B" )
            else:
                bar.configure(bg = '#3B3B3B')
        
class Engine(OpenGLFrame):
    # !!!OpenGlFrame requires adding own code to initgl and redraw!!!
    # !!!This solution only renders the F3D viewer, as it uses EXTERNAL, so controls need to be defined!!!
    def __init__(self, frame):
        super().__init__(frame)
        
        self.engine = None
        print(frame)
        
    # Initialize F3D
    def initgl(self):
        self.engine = f3d.Engine.create()  # use create_external_egl for Wayland
        self.engine.scene.add(r'FRCobots-V6.0 STEP Models/FRCobots-V6.0 STEP Models/FR5-WML-V6.0.STEP')

    def redraw(self):
        self.engine.window.render()

class GUI:
    def __init__(self):
        self.root = ttk.setup_master()
        self.root.title("Simulation Plotter")
        self.root.configure(background="white")
        self.root.geometry("1750x800")
        frame = Frame(self.root, borderwidth=5)
        frame.pack(expand=True, fill=BOTH)

        self.tests: list[Test3D] = []

        self._build(frame)
        
        
        self.root.mainloop()

    def _quit(self, *args):
        try:
            self.root.destroy()
        except:
            pass
        print('destroyed')

    def _create_menu(self):
        pass

    def _build(self, root: typing.Union[Frame, LabelFrame]):
        
        self._create_menu()

        # TODO: Check Device Connections
        
        dc_frame = create_frame(root,0,0,7,3,LabelFrame, text='DC Frame', relief=GROOVE, sticky=NSEW)

        # tab_frame: Tab Functions
        tab_frame = create_frame(root,0,3,1,6,LabelFrame, text='Tab Frame', relief=GROOVE, sticky=NSEW)

        # TODO: Open Automation Test
        # TODO: Arm Communication
        # TODO: Results
        # TODO:  Plotter

        #self.create_model(plot_frame, r'FRCobots-V6.0 STEP Models/FRCobots-V6.0 STEP Models/FR3-V6.0 Model.STEP')

        plot_frame = create_frame(root,1,3,6,6,LabelFrame, text='Plot Frame', relief=GROOVE, sticky=NSEW)
        self.plotter_notebook = ttk.Notebook(plot_frame)
        self.plotter_notebook.pack(expand=True, fill=BOTH)
        Button(plot_frame, text='start demo', command=lambda e=None: self._dummy_light_test()).pack()
        plotter_3d_frame = create_frame(self.plotter_notebook,1,3,6,6,Label, relief=GROOVE, sticky=NSEW)
        
        self.plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        
        
        self.plotter3d = Plotter3D(plotter_3d_frame)
        # TODO:  2D Plotter

        plotter_2d_frame = create_frame(self.plotter_notebook,1,3,6,6,Label, relief=GROOVE, sticky=NSEW)
        self.plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter2d = Plotter2D(plotter_2d_frame)

        # TODO Connection Status
        cs_frame = create_frame(root,7,0,1,9,LabelFrame, text='Connection Frame', relief=GROOVE, sticky=NSEW)
        connection_bar = ConnectionStatus(cs_frame, 0,0,1,1,4,1, sticky=SE)
        


        Scale(cs_frame, resolution=0.0001, label='Strength', from_=0.0, to=1.0, command=lambda e=0.0: connection_bar._update(e)).grid(row=1,column=1,sticky=E)
        
    def create_model(self, root, step):

        F3D = Engine(root)
        F3D.pack(fill=BOTH, expand=True)
        
        #    # For testing purposes only, exit after `timeout` seconds
        #    root.after(args.timeout * 1000, root.destroy)

    def _dummy_light_test(self):
        self.new_test('Dummy Light Test')
        for i in range(5):
            x         = numpy.random.rand()
            y         = numpy.random.rand()
            z         = numpy.random.rand()
            theta     = numpy.random.rand()
            phi       = numpy.random.rand()
            intensity = numpy.random.rand() 
            self.test.add_li(x, y, z, theta, phi, intensity)
            self.test.plot_light_intensity3D(self.plotter3d.ax)
            self.test.plot_light_intensity2D(self.plotter2d.ax)
            self.plotter3d.canvas.draw_idle()
            self.plotter2d.canvas.draw_idle()

    def new_test(self, test_name, maxsize=None):
        self.test = Test3D(test_name, maxsize, f"#{numpy.random.randint(0, 0xFFFFFF):06x}")
        self.tests.append(self.test)
        return self.test


class Test3D:
    def __init__(self, test_name:str, maxsize=None, color='blue'):
        self.color = color
        self.test_name = test_name
        self.maxsize=maxsize

        self.light_intensity: list[tuple[float, float, float, float, float, float]] = []
        '''[(x, y, z, rx, ry, rz), ...]'''
        self.path: list[tuple[float, float, float]] = []
        '''[(x,y,z), ...]'''

    def add_li(self, x, y, z, theta, phi, intensity):
        # Remove oldest index if maxsize is set and reached
        if self.maxsize is not None and self.light_intensity >= self.maxsize:
            self.light_intensity.pop(0)

        rx = intensity * numpy.cos(theta) * numpy.sin(phi)
        ry = intensity * numpy.sin(theta) * numpy.sin(phi)
        rz = intensity * numpy.cos(phi)

        self.light_intensity.append((x, y, z, rx, ry, rz))
    
    def plot_light_intensity3D(self, ax: axes.Axes, **options):
        
        for x, y, z, rx, ry, rz in self.light_intensity:
            ax.quiver(x, y, z, rx, ry, rz, color = self.color, **_is_attribute(ax.quiver, 'get', **options)) 
    
    def plot_light_intensity2D(self, ax: axes.Axes, **options):
        for x, y, z, rx, ry, rz in self.light_intensity:
            ax.scatter(x, y, c=self.color, **_is_attribute(ax.scatter, 'get', **options)) 
        

    def add_path(self, x, y, z):
        # Remove oldest index if maxsize is set and reached
        if self.maxsize is not None and self.path >= self.maxsize:
            self.path.pop(0)

        self.path.append((x, y, z))
    
class Plotter2D():
    def __init__(self, root, **options):
        self.root = root
        self.fig = Figure(figsize=(6, 5), dpi = 100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.toolbar_frame = Frame(self.root)
        self.toolbar_frame.pack(side=BOTTOM, expand=False, fill=X)
        toolbar_frame = Frame(self.toolbar_frame)
        toolbar_frame.pack(side=LEFT, expand=False, fill=X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        Button(self.toolbar_frame, text='Autoscale', command = no_function).pack(side=LEFT)
        self.ax.minorticks_on()
        self.ax.grid(True)
        
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(side=LEFT, fill=BOTH, expand = True)

    
    def _update_plot(self):
        self.ax.clear()

        self.canvas.draw()
 
class Plotter3D():
    def __init__(self, root, **options):
        self.root = root
        self.fig = Figure(figsize=(6, 5), dpi = 100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.toolbar_frame = Frame(self.root)
        self.toolbar_frame.pack(side=BOTTOM, expand=False, fill=X)
        toolbar_frame = Frame(self.toolbar_frame)
        toolbar_frame.pack(side=LEFT, expand=False, fill=X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        Button(self.toolbar_frame, text='Autoscale', command = no_function).pack(side=LEFT)
        
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(side=LEFT, fill=BOTH, expand = True)

    

    
    def _update_plot(self):
        self.ax.clear()

        self.canvas.draw()
       

if __name__ == '__main__':
    gui = GUI()

