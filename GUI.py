import os, glob, inspect
import typing
import dataclasses
import time


from tkinter import *
from tkinter import ttk, filedialog, colorchooser

from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.font_manager import FontProperties
import f3d
from pyopengltk import OpenGLFrame


import socket
import multiprocessing
import threading
import requests

import numpy
from labquest import LabQuest

try:
    from api.farinoAPI.fairino.Robot import RPC
except:
    from Robot import RPC
 
# To Save as an executable: pyinstaller --onefile GUI.py  

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
 
def _save_file(file_types = [("All Files", "*.*")]):
    all_file_types = ('All Files', tuple(file_type for _, file_type in file_types))
    if ("All Files", "*.*") in file_types:
        del file_types[file_types.index(("All Files", "*.*"))]

    return filedialog.asksaveasfile(
    title="Save Test Results",
    initialdir=os.path.dirname(__file__),  # Optional: Set initial directory
    filetypes=(*file_types, all_file_types)# Optional: Filter file types
    )

 
def _radius(x1,y1,z1,x2,y2,z2):
    return numpy.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
 
def _angle(x1,y1,z1,x2,y2,z2):
    r = _radius(x1,y1,z1,x2,y2,z2)
    theta = numpy.atan2(y1-y2, x1-x2)
    phi = numpy.arccos((z1-z2)/r)
    return phi, theta

def _toggle_frame(frame: typing.Union[Frame, LabelFrame], state=DISABLED):
    for child in frame.winfo_children():
        try:
            child.config(state=state)
        except:
            _toggle_frame(child, state)

def _reset_var(value, *vars: DoubleVar):
        for var in vars:
            var.set(value)


def _rotatex(x, y, z, angle):
    if numpy.isnan(angle):
        raise ValueError(f'Invalid angle: {angle}')
    nx = x
    ny = y * numpy.cos(angle) - z * numpy.sin(angle)
    nz = y * numpy.sin(angle) + z * numpy.cos(angle)
    return nx, ny, nz

def _rotatey(x, y, z, angle):
    if numpy.isnan(angle):
        raise ValueError(f'Invalid angle: {angle}')
    nx = x * numpy.cos(angle) + z * numpy.sin(angle)
    ny = y
    nz = -x * numpy.sin(angle) + z * numpy.cos(angle)
    return nx, ny, nz

def _rotatez(x, y, z, angle):
    if numpy.isnan(angle):
        raise ValueError(f'Invalid angle: {angle}')
    nx = x * numpy.cos(angle) - y * numpy.sin(angle)
    ny = x * numpy.sin(angle) + y * numpy.cos(angle)
    nz = z
    return nx, ny, nz


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

class Plotter2D():
    def __init__(self, root, **options):
        self.root = root
        self.fig = Figure(figsize=(6, 4), dpi = 100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.root)
        self.toolbar_frame = Frame(self.root)
        self.toolbar_frame.pack(side=BOTTOM, expand=True, fill=X)
        toolbar_frame = Frame(self.toolbar_frame)
        toolbar_frame.pack(side=LEFT, expand=True, fill=X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

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
       


class Communicator:
    def __init__(self, root: Frame):
        self.ip_var = StringVar()
        self.chat_var = StringVar()
        self.remote_socket = None
        self.listensocket  = None
        self.clientsocket = None
        self._build(root)

    def _build(self, root):
        self.root = root
    
        Connection_frame = Frame(self.root)
        Connection_frame.grid(row=0,column=0)

        text_frame = Frame(self.root)
        text_frame.grid(row=1,column=0)
        self.textbox = Text(text_frame, height=10, width=40)
        
        
        
        ys = ttk.Scrollbar(text_frame, orient = 'vertical', command = self.textbox.yview)
        xs = ttk.Scrollbar(text_frame, orient = 'horizontal', command = self.textbox.xview)
        self.textbox['yscrollcommand'] = ys.set
        self.textbox['xscrollcommand'] = xs.set

        self.textbox.grid(column = 0, row = 0, sticky = NSEW)
        xs.grid(column = 0, row = 1, sticky = EW)
        ys.grid(column = 1, row = 0, sticky = NS)

        self.host_button = Button(Connection_frame, text='Host Remote Connection', command=lambda e=None: self.start_server())
        self.host_button.grid(row=0, column=0, sticky=NSEW)
        self.ip_label = Label(Connection_frame, text='')
        self.ip_label.grid(row=0, column=2, sticky=NSEW)
        self.join_button = Button(Connection_frame, text='Join Remote Connection', command=lambda e=None: self._create_user_input_window())
        self.join_button.grid(row=0, column=3, sticky=NSEW)

        self.chat_entry = Entry(self.root, textvariable=self.chat_var)
        self.chat_entry.grid(row = 2, column=0, columnspan=3, sticky=NSEW, pady=12)
        self.chat_entry.bind('<Return>', lambda e=None: self.send_message())

    def start_server(self, maxConnections=1):
        '''
        MUST Enable Port Forwarding in internet providers settings for this device!!! set internal and external ports to 8000
        '''
        self.listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.host = '0.0.0.0'
        self.Port = 9000
        self.maxConnections = maxConnections
        self.ip = requests.get('https://api.ipify.org').text

        self.ip_label.configure(text=f'Host IP: {self.ip} Local IP: {socket.gethostbyname(socket.gethostname())}')
        self.host_button.config(text='Close Host', command=lambda e=None: self.close_server())
        self.join_button.config(state=DISABLED)

        self.listensocket.bind((self.host, self.Port))

        self.listensocket.listen(self.maxConnections)

        print(f'Server started at {self.ip} on port {self.Port}...')

        self.running = False
        
        listen_process = threading.Thread(target=self.pair_device, daemon=True)
        listen_process.start()

    def close_server(self):
        self.listensocket.close()
        self.ip_label.configure(text=f'')
        self.join_button.config(state=NORMAL)
        self.listensocket = None
        self.host_button.config(text='Host Remote Connection', command=lambda e=None: self.start_server())

    def _create_user_input_window(self):
        self.join_button.config(state=DISABLED)
        self.host_button.config(state=DISABLED)
        self.user_input_window = Toplevel(self.root, takefocus=True)
        #self.user_input_window.bind('<Destroy>', lambda e=None: self._user_input_destroyed())
        
        Label(self.user_input_window, text='Enter IP to join remote GUI').grid(row=0, column=0, columnspan=2, sticky=NSEW)
        Label(self.user_input_window, text='Host IP:').grid(row=1, column=0, sticky=NSEW)
        Entry(self.user_input_window, textvariable=self.ip_var).grid(row=1, column=1, sticky=NSEW)
        self.user_input_error_label = Label(self.user_input_window, text='')
        self.user_input_error_label.grid(row=2, column=0, columnspan=2, sticky=NSEW)

        
        self.remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.remote_connect_button = Button(self.user_input_window, text='Connect', command=lambda e=None: threading.Thread(target=self._remote_connection_attempt).start())
        self.remote_connect_button.grid(row=3, column=0, columnspan=2)

    def _remote_connection_attempt(self):
        self.remote_connect_button.config(state=DISABLED)
        port = 9000
        ip =  self.ip_var.get() #'192.168.1.141'
        try:
            self.remote_socket.connect((ip, port))
        except Exception as e:
            self.remote_connect_button.config(state=NORMAL)
            print(e)
            self.user_input_error_label.config(text=f'Unable to connect to {ip}')
            return
        
        self.user_input_window.destroy()

        listen_process = threading.Thread(target=self.listen, daemon=True, args= (self.remote_socket,))
        listen_process.start() 

    def _user_input_destroyed(self):
        self.join_button.config(state=NORMAL)
        self.host_button.config(state=NORMAL)

    def set_running(self, state=False):
        self.running = state

    def send_message(self):
        text = self.chat_var.get()
        self.write_message(f'{os.getlogin()} >>> {text}')

        try:
            if self.remote_socket:
                self.remote_socket.sendall(f'{os.getlogin()} <<< {text}'.encode())
        finally:
            pass

        try:
            if self.clientsocket:
                self.clientsocket.sendall(f'{os.getlogin()} <<< {text}'.encode())
        finally:
            pass
        self.chat_var.set('')
            
    def write_message(self, text):
        if self.textbox:
            self.textbox.insert(END, '\n')
            self.textbox.insert(END, text)
            self.textbox.see(END)

    def pair_device(self):
        while True:
            try:
                (self.clientsocket, self.address) = self.listensocket.accept()
            except OSError as e:
                print(f'Hosting ended...')
                break
            print(f'New connection made with {self.address}...')
            self.running = True
            listen_process = threading.Thread(target=self.listen, daemon=True, args= (self.clientsocket,))
            listen_process.start()

    def listen(self, clientsocket: socket):
        while True:
            try:
                message = clientsocket.recv(1024).decode()
                if len(message) == 0:
                    break
                self.write_message(message)
            except ConnectionResetError:
                return

class RobotCommunicator():
    def __init__(self):
        self.com = RPC()
        
        self.HOME = [0, -45, -133.25, -180, -90, 90]
        self.move_thread = None
        #self.home()
        #self.com.SetGripperConfig(1, 1, 0, 2)


        # Save Stop motion function in case of error. 
        # Will update to the current movement type's stop
        self.motion_stop = None

    def _set_gripper(self, state):
        pass
        #print(self.com.SetToolDO(0, 1 if state else 0))
        #error = self.com.MoveGripper(0, 90 if state else 0, 50, 50, 0, 0, 0, 0 ,0 ,0)
        #print(f"MoveGripper retval is:{error}")

    def _move(self, function):
        function()
        self.move_thread = None
        
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
        self._move_wait()

        

        funct = lambda: self.com.MoveL(
            desc_pos=self.com.GetActualTCPPose(0)[1],
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

        desc_pos = self.com.GetActualTCPPose(0)[1]
        dpos = [desc_pos[0]-x,desc_pos[3]-r, desc_pos[2]-z,0,0,0] 
        desc_pos=self.com.GetActualTCPPose(0)[1],
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

        funct = lambda: self.com.MoveL(desc_pos, tool, user, vel, acc, ovl, blendR, blendMode, exaxis_pos, search, offset_flag, offset_pos, oacc, velAccParamMode)
        self.move_thread = threading.Thread(target=self._move, args=(funct, ), daemon=True)
        self.move_thread.start()
 
    def home(self):
        self.stop()
        self._joint_move(self.HOME)

    def _joint_move(self, joint_pos):

        self._move_wait()
        tool=0
        user=0
        desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        vel = 20.0
        acc = 0.0
        ovl = 100.0
        exaxis_pos = [0.0,0.0,0.0,0.0]
        blendT = -1.0
        offset_flag = 0
        offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]

        funct = lambda: self.com.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
        self.move_thread = threading.Thread(target=self._move, args=(funct, ), daemon=True)
        self.move_thread.start()

        return False
    
    def _move_wait(self):
        while self.move_thread is not None:
            time.sleep(0.01)

    def square(self, dist, event=None):
        if event:
            _toggle_frame(event.widget, DISABLED)
        L = 20
        H = dist/L
        for i in range(L):
            print(f'Run {i+1} of {L}')
            self._incriment_move(0, dist, 0)
            self._move_wait()
            self._incriment_move(0, 0, H)
            self._move_wait()
            self._incriment_move(0, -dist, 0)
            self._move_wait()
            self._incriment_move(0, 0, H)
            self._move_wait()
        self._incriment_move(0, 0, -H*L*2)
        if event:
            _toggle_frame(event.widget, NORMAL)

    def _get_tool_position(self):
        ierr, tcp_pose = self.com.GetActualTCPPose()
        return tcp_pose

    def _get_joint_angles(self, degrees=True, flag=1):
        if degrees:
            joint_pos = self.com.GetActualJointPosDegree(flag)
        else:
            joint_pos = self.com.GetActualJointPosRadian(flag)
        if isinstance(joint_pos, int):
            return 0, 0, 0, 0, 0, 0
        return joint_pos[1]

    def _invk(self, x, y, z, rx, ry, rz, type=0):
        '''
        Perform inverse Kinematics for the tool to reach a certain position at a certain angle.

        type:
         0-absolute position (base coordinate system)
         1-relative position (base coordinate system)
         2-relative position (tool coordinate system)

        returns:
         [j1,j2,j3,j4,j5,j6]: inverse kinematics solution, Cartesian positional solution for joint positions
        '''
        ierr, join_pos = self.com.GetInverseKin(type, [x, y, z, rx, ry, rz], -1)
        #ierr, join_pos = self.com.GetInverseKinRef(type, [x, y, z, rx, ry, rz], joint_ref) # Might need
        if ierr:
            print(f'ERROR: {ierr}')
        return join_pos

    def _update_connection(self):
        while True:
            if not self.com.is_conect:
                self.com.reconnect()     
            else:
                return 
            time.sleep(5)

    def stop(self):
        print('stopping')
        self.com.StopMove()

class LightSensor():
    def __init__(self, freq=5000):
        self.freq = freq
        self.lq = None #LabQuest()
        self.status = -1
        self.rec = False

    def connect(self):
        self.status = self.lq.open()
        self.lq.select_sensors(ch1="lq_sensor")
        return self.status

    def close(self):
        try:
            self.lq.stop()
            self.lq.close()
        except:
            pass

    def start(self, freq=5000):
        self.freq = freq
        self.lq.start(period = int(1/self.freq*1000))
    
    def _avg(self, lux:list[float]):
        return sum(lux)/len(lux)
    
    def get_single(self):
        
        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))

        return self.lq.read('ch1')
    
    def get(self, Navg=1):
        '''
        Get sample of size N over avgn readings per sample returned
        '''

        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))
        data = self.lq.read_multi_pt('ch1', Navg)
        data = data if data else numpy.full(Navg, 0)
        return numpy.average(data)

    def test(self, avgn=1, chunk=1000, button:Button=None, linedata=None):
        if button:
            button.configure(state=DISABLED)

        t, lux = self.get(avgn, read_time=chunk/1000, linedata=linedata)
        le, c, re = self._find_edges(t, lux)

        if button:
            button.configure(state=NORMAL)
        print(f'Left: {le}, center: {c}, Right: {re}')
        return t, lux, le, c, re
        
    def _find_edges(self, times:list[float], lux: list[float]):
        assert len(times) == len(lux)

        peak = lux.index(max(lux))
        threshold = (max(lux) + min(lux)) / 2
        left_edge = right_edge = None
        for i in range(peak, 0, -1):
            if (lux[i - 1] - threshold) * (lux[i] - threshold) <= 0:
                left_edge = self.crossing(times[i - 1], lux[i - 1], times[i], lux[i], threshold)
                break

            for i in range(peak, len(lux) - 1):
                if (lux[i] - threshold) * (lux[i + 1] - threshold) <= 0:
                    right_edge = self.crossing(times[i], lux[i], times[i + 1], lux[i + 1], threshold)
                    break
        
        if left_edge is None or right_edge is None:
            center = None
            print("No two threshold crossings found.")
        else:
            center = (left_edge + right_edge) / 2
        return left_edge, center, right_edge 

    def crossing(self, x1, y1, x2, y2, level):
        if y1 == y2:
            return x1
        return x1 + (level - y1) * (x2 - x1) / (y2 - y1)

    def _plot_points(self, t:list[float], lux:list[float], linedata: tuple[FigureCanvasTkAgg, axes.Axes, Line2D]=None):
        
        if linedata is None:
            return
        canvas, ax, line = linedata
        line.set_xdata(t)
        line.set_ydata(lux)
        ax.relim()
        ax.autoscale_view()
        canvas.draw_idle()

class GUI:
    def __init__(self):
        self.robot = RobotCommunicator()
        self.ls = LightSensor()
        self.float_var = {}
        self.light_intensity: list[tuple[float, float]] = []

        self.stop_movement = False

        self.root: Tk = ttk.setup_master()
        self.root.title("Simulation Plotter")
        self.root.configure(background="white")
        self.root.geometry("800x800")
        frame = Frame(self.root, borderwidth=5)
        frame.pack(expand=True, fill=BOTH)

        self.light_record = False
        
        self._build(frame)

        self.test_data =TestData(self.robot, self.ls, self.TestSelection, self.plotter2d, self.plotter3d)

        self.root.protocol("WM_DELETE_WINDOW",  self._on_close)

        
        self.event = True
        
        threading.Thread(target=self._update_widgets, args=(self.connection_bar, self.robot_frame, self.joint_angle_label), daemon=True).start()
        #threading.Thread(target=self._constant_light_intensity, args=(10,), daemon=True).start()
        
        self.root.mainloop()
    
    def _on_close(self):
        self.event = False
        self.ls.close()
        self.communicator.set_running(False)
        self.root.destroy()      

    def _create_menu(self):
        pass

    def _build(self, root: typing.Union[Frame, LabelFrame]):
        
        self._create_menu()

        # Test Select frame
        ts_frame = create_frame(root,0,0,7,3,LabelFrame, text='Test Selection', relief=GROOVE, sticky=NSEW)
        self.TestSelection = Listbox(ts_frame, selectmode=MULTIPLE, )
        self.TestSelection.pack(expand=True, fill=BOTH)#.grid(row=0, column=0, columnspan=2, sticky=NSEW)
        self.TestSelection.bind('<<ListboxSelect>>', lambda e=None: self.test_data._plot_selected())

        # tab_frame: Tab Functions
        tab_frame = create_frame(root,0,3,1,6,LabelFrame, text='Tab Frame', relief=GROOVE, sticky=NSEW)

        self.tabs = ttk.Notebook(tab_frame)
        self.tabs.pack(expand=True, fill=BOTH)
        
        # TODO: Open Automation Test
        test_frame = create_frame(self.tabs, 1,1,1,1,LabelFrame, relief=GROOVE, sticky=NSEW)
        self.tabs.add(test_frame, text='Tests')
        self._build_test_page(test_frame)

        # TODO: Arm Communication
        self.robot_frame = create_frame(self.tabs, 1,1,1,1,LabelFrame, relief=GROOVE, sticky=NSEW)
        self.tabs.add(self.robot_frame, text='Robot')
        self._build_robot_controller(self.robot_frame)

        


        # TODO: Results
        # TODO:  Plotter

        #self.create_model(plot_frame, r'FRCobots-V6.0 STEP Models/FRCobots-V6.0 STEP Models/FR3-V6.0 Model.STEP')

        plot_frame = create_frame(self.tabs,1,3,6,6,LabelFrame, relief=GROOVE, sticky=NSEW)
        self.tabs.add(plot_frame, text='Results')
        self.plotter_notebook = ttk.Notebook(plot_frame)
        self.plotter_notebook.pack(expand=True, fill=BOTH)
        
        plotter_3d_frame = create_frame(self.plotter_notebook,1,3,6,6,Label, relief=GROOVE, sticky=NSEW)
        
        self.plotter_notebook.add(plotter_3d_frame, text='3D Plotter')
        
        
        self.plotter3d = Plotter3D(plotter_3d_frame)
        # TODO:  2D Plotter

        plotter_2d_frame = create_frame(self.plotter_notebook,1,3,6,6,Label, relief=GROOVE, sticky=NSEW)
        self.plotter_notebook.add(plotter_2d_frame, text='2D Plotter')
        self.plotter2d = Plotter2D(plotter_2d_frame)

        # TODO Connection Status
        cs_frame = create_frame(root,7,0,1,9,LabelFrame, text='Connection Frame', relief=GROOVE, sticky=NSEW)
        text_frame = create_frame(cs_frame,0,0,5,1,LabelFrame, text='Connection Chat', relief=GROOVE, sticky=NSEW)
        self.communicator = Communicator(text_frame)

        



        self.connection_bar = ConnectionStatus(cs_frame, 0,0,1,1,4,1, sticky=SE)
    
    def _build_test_page(self, root:Frame):
        self.float_var['test'] = {}

        lr_frame = LabelFrame(root, text='Light Reading Settings')
        lr_frame.grid(row=0,column=0, sticky=NSEW)

        # Create Entry Boxes
        settings = (('Frequency', 5000), ('Data Points', 1000), ('Average', 1))
        for row, (setting, default) in enumerate(settings):
            self.float_var['test'][setting] = IntVar(value=default)
            Label(lr_frame, text=f'{setting.capitalize()}:').grid(row=row, column=0)
            Entry(lr_frame, textvariable=self.float_var['test'][setting]).grid(row=row, column=1)

        light_test_button = Button(lr_frame, text='Start New Test', command=lambda e=None: self._light_test(light_test_button))
        light_test_button.grid(row=len(settings),column=1)
        Button(lr_frame, text='Dummy Test', command=lambda e=None: self.test_data._dummy_test(100, 5)).grid(row=len(settings), column=2)
        
        Button(lr_frame, text='Save Tests', command=lambda e=None: self.test_data._save_test()).grid(row=len(settings), column=3)
        Button(lr_frame, text='Open Tests', command=lambda e=None: self.test_data._open_file()).grid(row=len(settings), column=4)
        
        #Button(lr_frame, text='Save Tests', command=lambda e=None: self.test_data.write_test_to_file('Dummy_test_data.tst', [0, self.test_data.cur_move_id])).grid(row=len(settings), column=3)
        #Button(lr_frame, text='Open Tests', command=lambda e=None: self.test_data.extract_test_file('Dummy_test_data2.tst')).grid(row=len(settings), column=4)
        

        lrp_frame = LabelFrame(root, text='Light Reading Settings')
        lrp_frame.grid(row=0, column=1, rowspan=5, sticky=NSEW)
        self.test_plot = Plotter2D(lrp_frame)

    def _light_test(self, button):
        line = self.test_plot.ax.plot([],[])[0]
        thread = threading.Thread(target= self.ls.test, args=(1, 1000, button, (self.test_plot.canvas, self.test_plot.ax, line)), daemon=True)
        thread.start()

    def _build_robot_controller(self, root:Frame):
        
        # Create float var for position entry boxes
        self.float_var['robot'] = {}
        position_frame = LabelFrame(root, text='Current Position')
        position_frame.grid(row=0,column=0, sticky=NSEW)

        # Create Entry Boxes
        for row, axis in enumerate(('x', 'y', 'z')):
            self.float_var['robot'][axis] = DoubleVar()
            Label(position_frame, text=f'{axis.capitalize()}:').grid(row=row, column=0)
            Entry(position_frame, textvariable=self.float_var['robot'][axis]).grid(row=row, column=1)


        incrimental_frame = LabelFrame(root, text='Current Position')
        incrimental_frame.grid(row=1,column=0, sticky=NSEW)

        # Create Entry Boxes
        for row, axis in enumerate(('dx', 'dy', 'dz')):
            self.float_var['robot'][axis] = DoubleVar()
            Label(incrimental_frame, text=f'{axis}:').grid(row=row, column=0)
            Entry(incrimental_frame, textvariable=self.float_var['robot'][axis]).grid(row=row, column=1)

        Button(incrimental_frame, text='Reset', command=lambda e=None: _reset_var(0.0, *(self.float_var['robot'][axis] for axis in ('dx', 'dy', 'dz')))).grid(row=2, column=2)
        Button(incrimental_frame, text='Run', command=lambda e=None: self.robot._incriment_move(*(self.float_var['robot'][axis].get() for axis in ('dx', 'dy', 'dz')))).grid(row=2, column=3)

        

        self.joint_angle_label = Label(root, text = '')
        self.joint_angle_label.grid(row = 2, column=0)
        Button(root, text='Home', command=lambda e=None: self.robot.home()).grid(row=3, column=1)
        Button(root, text='Square', command=lambda e=None: threading.Thread(target=self.square_test, args=(100,e)).start()).grid(row=3, column=2)
        Button(root, text='Stop', command=lambda e=None: self.robot.stop()).grid(row=3, column=3)
        checkvar_val = BooleanVar(value=False)
        Checkbutton(root, text='Set Gripper', command=lambda e=None: self.robot._set_gripper(checkvar_val.get()), variable=checkvar_val).grid(row=3, column=4)
        self._update_joint_angle_label()
    
    def _update_joint_angle_label(self):
        j1, j2, j3, j4, j5, j6 = self.robot._get_joint_angles(True)
        self.joint_angle_label.config(text=f'Joint Angles:\nj1 = {j1}\n j2 = {j2}\n j3 = {j3}\n j4 = {j4}\n j5 = {j5}\n j6 = {j6}\n')

    def _update_widgets(self, status: ConnectionStatus, frame: Frame, joint_label: Label):
        frame_disabled = False
        reconnect_thread = threading.Thread(target=self.robot._update_connection, daemon=True)
        while True:
            time.sleep(0.5)
            
            strength = 1.0 if self.robot.com.is_conect else 0.0
            status._update(strength)
            
            if strength == 0.0:
                frame_disabled = True
                _toggle_frame(frame, DISABLED)
                if not reconnect_thread.is_alive():
                    reconnect_thread = threading.Thread(target=self.robot._update_connection, daemon=True)
                    reconnect_thread.start()
            elif frame_disabled:
                frame_disabled = False
                _toggle_frame(frame, NORMAL)

            if self.robot.com.is_conect:
                j1, j2, j3, j4, j5, j6 = self.robot._get_joint_angles(True)
                joint_label.config(text=f'Joint Angles:\nj1 = {j1}\n j2 = {j2}\n j3 = {j3}\n j4 = {j4}\n j5 = {j5}\n j6 = {j6}\n')

    def create_model(self, root, step):

        F3D = Engine(root)
        F3D.pack(fill=BOTH, expand=True)

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

    def _constant_light_intensity(self, freq):
        period = 1/freq
        
        while self.event:
            time.sleep(period)
            if self.robot.com.is_conect:
                pos = self.robot._get_tool_position()
                intensity = self.ls.get_single()
                self.light_intensity.append((pos, intensity))

                x, y, z, rx, ry, rz = pos
                self.plot_point(x, y, z)

    def square_test(self, dist, event=None):
        def _test(freq, Navg, widget=None):
            try:
                if widget:
                    _toggle_frame(widget, DISABLED)
                L = 3
                H = dist/L
                self.test_data.start_recording(freq, Navg, 'Square_test')
                for i in range(L):
                    print(f'Run {i+1} of {L}')
                    self.test_data.next_movement(0, dist, 0)
                    self.robot._incriment_move(0, dist, 0)
                    self.robot._move_wait()
                    if not self.stop_movement: raise AssertionError

                    self.test_data.next_movement(0, 0, H)
                    self.robot._incriment_move(0, 0, H)
                    self.robot._move_wait()
                    if not self.stop_movement: raise AssertionError

                    self.test_data.next_movement(0, -dist, 0)
                    self.robot._incriment_move(0, -dist, 0)
                    self.robot._move_wait()
                    if not self.stop_movement: raise AssertionError

                    self.test_data.next_movement(0, 0, H)
                    self.robot._incriment_move(0, 0, H)
                    self.robot._move_wait()
                    if not self.stop_movement: raise AssertionError

                self.test_data.end_recording()

                self.robot._incriment_move(0, 0, -H*L*2)

                if event:
                    _toggle_frame(widget, NORMAL)
                    pass
            except AssertionError:
                self.test_data.end_recording()
                return

        thread = threading.Thread(target=_test, args=(5000, 1), daemon=True)
        thread.start()
        
    def plot_point(self, x, y, z):
        self.plotter3d.ax.scatter(x, y, z)
        self.plotter3d.canvas.draw_idle()


class TestData:
    def __init__(self, robot:RobotCommunicator, ls:LightSensor, cb:Listbox=None, plotter2d: Plotter2D=None, plotter3d: Plotter3D=None):
        self.robot = robot
        self.ls = ls
        self.cb = cb
        self.plotter2d = plotter2d
        self.plotter3d = plotter3d

        self.test_results: dict[str, list[tuple[numpy.ndarray, list[numpy.ndarray]]]] = {None: []} 

        self.current_test_name = None

        self.data = []
        self._test_lines: dict[int, dict[str, Line2D]] = {}
        self.moving = False
        self.thread = None

        self.pos = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # [x, y, z, rx, ry, rz]
        self.offset = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self._setup_plots()
    
    def _setup_plots(self):
        self.plotter2d.ax.set_xlabel('Time (s)')
        self.plotter2d.ax.set_ylabel('Light Intensity (lumen)')
        #self.plotter2d.ax.legend().set_visible(True)

        self.plotter3d.ax.set_xlabel('x (mm)')
        self.plotter3d.ax.set_ylabel('y (mm)')
        self.plotter3d.ax.set_zlabel('z (mm)')
        #self.plotter3d.ax.legend().set_visible(True)

    @property
    def cur_move_id(self):
        return len(self.test_results[self.current_test_name])-1
        
    def result(self, move_id, test_name=None, flat=False):
        test_name = test_name if test_name else self.current_test_name
        movement, test_data = self.test_results[test_name][move_id]
        if flat:
            return test_data
        return self.individualize(test_data)
    
    def individualize(self, data):
        t, intensities, x, y, z, rx, ry, rz = zip(*data)
        return (numpy.array(t), numpy.array(intensities), numpy.array(x), numpy.array(y), numpy.array(z), numpy.array(rx), numpy.array(ry), numpy.array(rz))
    
    def set_pos(self, x, y, z, rx, ry, rz):
        self.pos = numpy.array([x, y, z, rx, ry, rz])
        self.offset = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
    def _interpolate(self, test_data, start_pos, offset):
        interpolated_data = []
        incriment = offset/max(len(test_data),1)
        for i, (t, intensity) in enumerate(test_data):
            pos = start_pos + incriment*i
            interpolated_data.append((t, intensity, *pos)) # TODO (time, intensity, x, y, z, rx, ry, rz)

        return interpolated_data
        
    def start_recording(self, freq, Navg, test_name:str=None):
        if self.current_test_name is not None:
            raise AssertionError("A test is already recording...")
        
        if test_name is None:
            test_name = f'Test {max(len(self.test_results)-1, 0)}'
        self.current_test_name = test_name

        self.test_results.setdefault(self.current_test_name, [])

        self.moving = True
        self.data = []
        self.thread = threading.Thread(target=self._record, args=(freq, Navg), daemon=True)
        self.thread.start()

    def pause_recording(self):
        self.moving = False
        self.pause_time = time.time()
    
    def resume_recording(self):
        self.moving = True
        self.start_time += time.time()
    
    def next_movement(self, dx=0.0, dy=0.0, dz=0.0, drx=0.0, dry=0.0, drz=0.0):
        self.moving = False
        time.sleep(0.01)
        data = self._interpolate(self.data, self.pos, self.offset)
        self.test_results[self.current_test_name].append((self.offset, data))
        
        label = f'Movement:{",".join(map(str, self.offset))}'
        self.plot_2d_data(data, self.current_test_name, self.cur_move_id, label)
        self.plot_3d_data(data, self.current_test_name, self.cur_move_id, label)

        self.pos += self.offset
        self.offset = numpy.array([dx, dy, dz, drx, dry, drz])
        self.moving = True
        return data
    
    def end_recording(self):
        self.moving = False

        # No test ongoing
        if self.current_test_name is None:
            return
        
        test_name = self.current_test_name
        self.current_test_name = None
        
        

        # wait some time so _record thread ends
        time.sleep(0.01)
        self.thread.join()

        data = self._interpolate(self.data, self.pos, self.offset)
        self.test_results[self.current_test_name].append((self.offset, data))
        
        label = f'Movement {self.cur_move_id}:{",".join(map(str, self.offset))}'
        self.plot_2d_data(data, self.current_test_name, self.cur_move_id, label)
        self.plot_3d_data(data, self.current_test_name, self.cur_move_id, label)

        self.pos += self.offset
        self.offset = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        self.cb.insert(END, f'Test {test_name} - {self.cur_move_id}')
        self.cb.selection_set(END)
        return  self.test_results[self.current_test_name]

    def _record(self, freq, Navg):
        period = 1/freq
        self.start_time = time.time()
        while self.current_test_name is not None:
            time.sleep(period)
            if self.moving:
                self.data.append((time.time()- self.start_time, self.ls.get(Navg)))

    def plot_3d_data(self, data, test_name, movement, label):
        if not self.plotter3d:
            return
        if data == []:
            return
        self._test_lines.setdefault(test_name, {})
        self._test_lines[test_name].setdefault(movement, {'3D': None, '2D': None})
        t, intensities, x, y, z, rx, ry, rz = zip(*data)
        intensities = numpy.array(intensities)/max(intensities)
        intensities[intensities < 0.5] = 0

        self._test_lines[test_name][movement]['3D']= self.plotter3d.ax.scatter(x, y, z, cmap='plasma', c=intensities, label=label)
        
        self.plotter2d.canvas.draw_idle()

    def plot_2d_data(self, data, test_name, movement, label):
        if not self.plotter2d:
            return
        if data == []:
            return
        self._test_lines.setdefault(test_name, {})
        self._test_lines[test_name].setdefault(movement, {'3D': None, '2D': None})
        t, intensities, x, y, z, rx, ry, rz = zip(*data)
        intensities = numpy.array(intensities)/max(intensities)
        self._test_lines[test_name][movement]['2D'] = self.plotter2d.ax.plot(t, intensities, label=label)[0]
        
        self.plotter2d.canvas.draw_idle()

    def show_results(self, test_id: typing.Union[int, tuple, list]):
        if not self.cb:
            return
        if isinstance(test_id, int):
            self._toggle_test_line(test_id, True)

        if isinstance(test_id, tuple):
            for id_ in test_id:
                self._toggle_test_line(id_, True)
        
        if isinstance(test_id, list):
            # from [id1:id2]
            if len(test_id) == 2:
                for id_ in range(test_id[0], test_id[1]+1):
                    self._toggle_test_line(id_, True)
            else:
                for id_ in test_id:
                    self._toggle_test_line(id_, True)

    def _toggle_test_line(self, test_name, movement, state=True):
        if not self.cb:
            return
        if self._test_lines[test_name][movement]['3D'] is not None:
            self._test_lines[test_name][movement]['3D'].set_visible(state)
        if self._test_lines[test_name][movement]['2D'] is not None:
            self._test_lines[test_name][movement]['2D'].set_visible(state)

    def _plot_selected(self):
        if not self.cb:
            return
        selected_indices = self.cb.curselection()
        # Use get(index) to retrieve the text for each index
        selected_tests = [str(self.cb.get(i).split('Test ')[-1].split(' - ')[0]) for i in selected_indices]
        selected_movements = [int(self.cb.get(i).split(' - ')[-1]) for i in selected_indices]

        for test_name in self._test_lines:
            for movement in self._test_lines[test_name]:
                self._toggle_test_line(test_name, movement, test_name in selected_tests and movement in selected_movements)

        self.plotter2d.canvas.draw_idle()
        self.plotter3d.canvas.draw_idle()


    def _save_test(self):
        f = _save_file([("Test Data", "*.tst"), ("xrb Test Data", "*.xrb")])

        if not f:
            return
        f.write(f'// Time, Intensity, x, y, z, rx, ry, rz\n')
            
        test = self.test_results.get(self.current_test_name, None)
        if test:
            f.write(f'// Test: {self.current_test_name} \n')
            for movement, data in test:
                label = f'Movement:{",".join(map(str, movement))}'
                f.write(f'// Movement: {label} \n')
                for dat in data:
                    f.write(f'{",".join(map(str, dat))}\n')

    def _open_file(self):
        files = _get_user_file(file_types=[("Test Data", "*.tst"), ("xrb Test Data", "*.xrb")])
        for file in files:
            self.extract_test_file(file)

    def write_test_to_file(self, filename, test_name:str):


        with open(filename, 'w') as f:
            #write header
            f.write(f'// Time, Intensity, x, y, z, rx, ry, rz\n')
            
            test = self.test_results.get(test_name, None)
            if test:
                movement, data = test
                label = f'Movement:{",".join(map(str, movement))}'
                f.write(f'// Movement: {label} \n')
                for dat in data:
                    f.write(f'{",".join(map(str, dat))}\n')
            
    def extract_test_file(self, filename):
        extracted_data: dict[str, list] = {}
        movement = None
        move_data = []
        with open(filename, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if index == 0:
                    continue
                if '// Test' in line:
                    test_name = str(line.split('// Test ')[-1].replace('\n','').rstrip())
                    print(f'Extracting Test {test_name}...')
                    extracted_data.setdefault(test_name, [])
                    continue
                if '// Movement:' in line:
                    if movement:
                        extracted_data[test_name].append((movement, move_data))

                    move_data = []
                    movement = tuple(map(float, line.split('// Movement:')[-1].split(',')))
                    print(f'Extracting {test_name} Movement {movement}...')
                    continue
                move_data.append(tuple(map(float, line.split(','))))
                
        
        for test_name in extracted_data:
            test = extracted_data[test_name]
            self.test_results[test_name] = test
            for i, (movement, data) in enumerate(test):
                label = f'Movement:{",".join(map(str, movement))}'
                self.plot_2d_data(data, test_name, i, label)
                self.plot_3d_data(data, test_name, i, label)
                self.cb.insert(END, f'Test {test_name} - {i}')
                self.cb.selection_set(END)
                self.current_test_name = test_name
        return extracted_data.values()

    def _dummy_test(self, L, N):
        self.data = []
        start_index = self.cur_move_id + 1
        filename = 'Dummy_test_data3.tst'
        self.test_name = 'Test 1'
        self.test_results[self.test_name] = []
        for i in range(N):
            for j in range(L):
                self.data.append((*numpy.random.randn(8), ))
            self.test_results[self.test_name].append((*numpy.random.randn(6), self.data))
            self.data = []
        self.write_test_to_file(filename, self.test_name)
        self.extract_test_file(filename)
        return self.data                


if __name__ == '__main__':
    gui = GUI()

