import os, glob, inspect
import typing
import dataclasses
import time


from tkinter import *
from tkinter import ttk, filedialog, colorchooser

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.font_manager import FontProperties
import f3d
from pyopengltk import OpenGLFrame
import matplotlib.axes as axes

import socket
import multiprocessing
import threading
import requests

import numpy
from labquest import LabQuest

from api.farinoAPI.fairino.Robot import *
 
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

class communicator:
    def __init__(self, root: Frame):
        self.ip_var = StringVar()
        self.chat_var = StringVar()
        self.remove_socket = None
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
        self.listensocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.host = '0.0.0.0'
        self.Port = 8000
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
        self.user_input_window.bind('<Destroy>', lambda e=None: self._user_input_destroyed())
        
        Label(self.user_input_window, text='Enter IP to join remote GUI').grid(row=0, column=0, columnspan=2, sticky=NSEW)
        Label(self.user_input_window, text='Host IP:').grid(row=1, column=0, sticky=NSEW)
        Entry(self.user_input_window, textvariable=self.ip_var).grid(row=1, column=1, sticky=NSEW)
        self.user_input_error_label = Label(self.user_input_window, text='')
        self.user_input_error_label.grid(row=2, column=0, columnspan=2, sticky=NSEW)

        
        self.remove_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.remote_connect_button = Button(self.user_input_window, text='Connect', command=lambda e=None: threading.Thread(target=self._remote_connection_attempt).start())
        self.remote_connect_button.grid(row=3, column=0, columnspan=2)


    def _remote_connection_attempt(self):
        self.remote_connect_button.config(state=DISABLED)
        port = 8000
        ip = self.ip_var.get()
        try:
            self.remove_socket.connect((ip, port))
        except Exception as e:
            self.remote_connect_button.config(state=NORMAL)
            print(e)
            self.user_input_error_label.config(text=f'Unable to connect to {ip}')
            return
        self.user_input_window.destroy()

        listen_process = threading.Thread(target=self.listen, daemon=True, args= (self.remove_socket,))
        listen_process.start()


        self.remote_connect_button.config(state=NORMAL)

    def _user_input_destroyed(self):
        self.join_button.config(state=NORMAL)
        self.host_button.config(state=NORMAL)

    def _remote_connection(self):
        pass

    def set_running(self, state=False):
        self.running = state


    def send_message(self):
        text = self.chat_var.get()
        self.write_message(text)

        try:
            if self.remove_socket:
                self.remove_socket.sendall(text.encode())
        finally:
            pass

        try:
            if self.clientsocket:
                self.clientsocket.sendall(text.encode())
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
            message = clientsocket.recv(1024).decode()
            if len(message) == 0:
                break
            self.write_message(message)

class RobotCommunicator():
    def __init__(self):
        self.com = RPC()
        
        self.HOME = [0, -125.517, 124.552, 3.64, 85.43, 95.241]
        #self.home()


        # Save Stop motion function in case of error. 
        # Will update to the current movement type's stop
        self.motion_stop = None

    def _incriment_move(self, dx, dy, dz, ref=4, vel=20.0, acc=100.0, *vars):
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
        self.motion_stop = self.com.StopMotion
        print(f'Moving by {(dx, dy, dz)}')
        current_pose = numpy.array(self.com.GetActualTCPPose(0)[1])
        new_pose = current_pose + numpy.array([dx, dy, dz, 0, 0, 0])
        print(new_pose)
        joint_pos = self._invk(*new_pose, type=0)
        print(joint_pos)


        self._joint_move(joint_pos, tool=0)

        self.motion_stop = None
        return False
    
    def _position_move(self, x, y, z, ref=4, vel=20.0, acc=100.0, *vars):
        '''
        '''
        self.motion_stop = self.com.StopMotion
        ierr = self.com.MoveL([], vel, acc)
        if ierr:
            self.motion_stop()
            print(ierr)
            return True

        self.motion_stop = None
        return False
    
    def home(self):
        self._joint_move(self.HOME)

    def _joint_move(self, joint_pos, tool=0, user=0, desc_pos = [0.0,0.0,0.0,0.0,0.0,0.0,0.0], vel = 20.0, acc = 0.0, 
                    ovl = 100.0, exaxis_pos = [0.0,0.0,0.0,0.0], blendT = -1.0, offset_flag = 0, offset_pos = [0.0,0.0,0.0,0.0,0.0,0.0]):
        '''
        '''
        self.motion_stop = self.com.StopMotion
        ierr = self.com.MoveJ(joint_pos, tool, user, desc_pos, vel, acc, ovl, exaxis_pos, blendT, offset_flag, offset_pos)
        if ierr:
            self.motion_stop()
            print(ierr)
            return True

        self.motion_stop = None
        return False
    
    def square(self, dist):

        self._incriment_move(0, dist, 0)
        self._incriment_move(0, 0, dist)
        self._incriment_move(0, -dist, 0)
        self._incriment_move(0, 0, -dist)


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

class LightSensor():
    def __init__(self, freq=5000):
        self.freq = freq
        self.lq = LabQuest()
        self.status = -1
        self.rec = False
        

    def connect(self):
        self.status = self.lq.open()
        self.lq.select_sensors(ch1="lq_sensor")
        return self.status

    def close(self):
        self.lq.stop()
        self.lq.close()

    def start(self, freq=5000):
        self.freq = freq
        self.lq.start(period = int(1/self.freq*1000))
    
    def _avg(self, lux:list[float]):
        return sum(lux)/len(lux)
    
    def get(self, avgn=1, N=None, read_time=None, linedata=None):
        '''
        Get sample of size N over avgn readings per sample returned
        '''
        lux=[]
        t=[]
        assert N or read_time

        if self.status == -1:
            self.connect()
            self.lq.start(period=int(1/self.freq*1000))
        if N:
            for n in range(N):
                reading = self.lq.read_multi_pt('ch1', avgn)
                lux.append(self._avg(reading if reading else [0]))
                t.append(1/self.freq*n*avgn)
        elif read_time:
            start_time = time.time()
            while time.time() - start_time < read_time:
                reading = self.lq.read_multi_pt('ch1', avgn)
                lux.append(self._avg(reading if reading else [0]))
                t.append(time.time()-start_time)

        self._plot_points(t, lux, linedata)
        self.rec = False
        return (t, lux)

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

        self.root: Tk = ttk.setup_master()
        self.root.title("Simulation Plotter")
        self.root.configure(background="white")
        self.root.geometry("800x800")
        frame = Frame(self.root, borderwidth=5)
        frame.pack(expand=True, fill=BOTH)
        
        self.tests: list[Test3D] = []

        self._build(frame)
        self.root.protocol("WM_DELETE_WINDOW",  self._on_close)

        

        task = threading.Thread(target=self._update_connection_status, args=(self.connection_bar,), daemon=True)
        task.start()

        self.root.mainloop()

    def _on_close(self):
        self.ls.close()
        self.communicator.set_running(False)
        self.root.destroy()
        

    def _create_menu(self):
        pass

    def _build(self, root: typing.Union[Frame, LabelFrame]):
        
        self._create_menu()

        # TODO: Check Device Connections
        
        dc_frame = create_frame(root,0,0,7,3,LabelFrame, text='DC Frame', relief=GROOVE, sticky=NSEW)

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
        Button(plot_frame, text='start demo', command=lambda e=None: self._dummy_light_test()).pack()
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
        self.communicator = communicator(text_frame)

        



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
        Button(root, text='Square', command=lambda e=None: self.robot.square(100)).grid(row=3, column=2)
        self._update_joint_angle_label()
    
    def _update_joint_angle_label(self):
        j1, j2, j3, j4, j5, j6 = self.robot._get_joint_angles(True)
        self.joint_angle_label.config(text=f'Joint Angles:\nj1 = {j1}\n j2 = {j2}\n j3 = {j3}\n j4 = {j4}\n j5 = {j5}\n j6 = {j6}\n')

    
        
    def _update_connection_status(self, status: ConnectionStatus):
        frame_disabled = False
        while True:
            strength = 1.0 if self.robot.com.is_conect else 0.0
            status._update(strength)
            if strength == 0.0:
                frame_disabled = True
                _toggle_frame(self.robot_frame, DISABLED)
            elif frame_disabled:
                frame_disabled = False
                _toggle_frame(self.robot_frame, NORMAL)

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
       

if __name__ == '__main__':
    gui = GUI()

