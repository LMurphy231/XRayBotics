import dataclasses
import logging
import os
import inspect
import tkinter as tk
from tkinter import ttk, colorchooser
from functools import wraps
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, Literal
from matplotlib.artist import ArtistInspector, Artist

import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.collections import PathCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3D, Line3DCollection

P = ParamSpec("P")
R = TypeVar("R")

def copy_params(source: Callable[P, Any]) -> Callable[[Callable[..., R]], Callable[P, R]]:
    def decorator(target: Callable[..., R]) -> Callable[P, R]:
        return target
    return decorator

global Rz
global Ry
global Rx

def Rz(angle): 
    return np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle),  np.cos(angle), 0],
        [0          ,  0          , 1],
    ])
def Ry(angle): 
    return np.array([
        [np.cos(angle)  ,   0 , np.sin(angle)],
        [0              ,   1 , 0          ],
        [-np.sin(angle) ,   0 , np.cos(angle)],
    ])
def Rx(angle): 
    return np.array([
        [1, 0            ,   0           ],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle),  np.cos(angle)],
    ])

@dataclasses.dataclass
class DenavitHartenbergParameter:
    jointid: int
    theta: float
    a: float
    d:float
    alpha:float
    mass: float
    center_of_mass:np.ndarray[float]
    set_angle:float = 0.0
    type:str = 'rotational'


global FR5Joints 
FR5Joints = [
    DenavitHartenbergParameter(1, 0, 0   , 152,  np.pi/2, 4.64 , np.array([-0.19 , -18.28, 2.26  ])),
    DenavitHartenbergParameter(2, 0, -425, 0  , 0       , 10.08, np.array([212.47, 0     , 121.2 ])),
    DenavitHartenbergParameter(3, 0, -395, 0  , 0       , 2.71 , np.array([122.62, 0.17  , 12.59 ])),
    DenavitHartenbergParameter(4, 0, 0   , 102,  np.pi/2, 1.56 , np.array([0.05  , -2.33 , 14.68 ])),
    DenavitHartenbergParameter(5, 0, 0   , 102, -np.pi/2, 1.56 , np.array([-0.05 , 2.33  , 14.68 ])),
    DenavitHartenbergParameter(6, 0, 0   , 102, 0       , 0.36 , np.array([0.93  , 0.81  , -20.05])),
]



def rotate(matrix1, *rotation_matricies):
    for matrix2 in rotation_matricies:
        matrix1 = np.matmul(matrix1, matrix2)
    return matrix1

def rotate_point(point:np.ndarray, rotation_matrix:np.ndarray):
    return rotation_matrix @ point

def transformation_matrix(DH:DenavitHartenbergParameter, set_angle=None):
    if set_angle is not None:
        DH.set_angle = set_angle

    A = rotate(Rz(DH.set_angle),Rx(DH.alpha))
    B = np.array([[
        DH.a*np.cos(DH.set_angle),
        DH.a*np.sin(DH.set_angle),
        DH.d
        ]]).T
    C = np.array([[0,0,0]])
    D = np.array([[1]]) 
    return np.block([
            [A,B], 
            [C,D]
           ])


def deltaTheta(Jacobian, deltaX, damping_factor):
    [U, S, Vh] = np.linalg.svd(Jacobian, full_matrices=False,)
    #print(f'U:\n{U}\nS:\n{S}\nV:\n{V}')
    
    #sigma = np.diag(S)

    sigma_inv = S / (S**2 + damping_factor**2)
    #J_plus = np.matmul(np.matmul(V.T, np.diag(sigma_inv)), U.T)
    
    dTheta = Vh.T @ np.diag(sigma_inv) @ U.T @ deltaX
    return dTheta
    return np.matmul(J_plus, deltaX)

def ForwardKinematics(DHArray:list[DenavitHartenbergParameter], set_values:list[float]):
    T = np.eye(4)
    for i in range(len(DHArray)):
        arr = transformation_matrix(DHArray[i], set_values[i])
        T = np.matmul(T, arr)

    return T

def JacobianMatrix(DHArray:list[DenavitHartenbergParameter], set_values):
    Z = np.full((3, len(DHArray)+1), 0.0)
    O = np.full((3, len(DHArray)+1), 0.0)
    Z[:, 0] = np.array([0,0,1], dtype=float).T
    O[:, 0] = np.array([0,0,0], dtype=float).T
    n = len(DHArray)
    Jacobian = np.full((6,n), 0.0)
    
    for i in range(n):
        T = ForwardKinematics(DHArray[:i+1], set_values[:i+1])
        Z[:, i+1] = T[:-1, 2]
        O[:, i+1] = T[:-1, 3]

    
    On = O[:, -1]
    for i in range(n):
        
        if DHArray[i].type == "rotational":
            Jacobian[:3,i] = np.linalg.cross(Z[:, i], On-O[:, i])
            Jacobian[3:6,i] = Z[:, i]
        else:
            Jacobian[:3,i] = Z[:, i]
            Jacobian[3:6,i] = np.array([0,0,0], dtype=float).T
    
    return Jacobian

def IterativeInvK(DHArray:list[DenavitHartenbergParameter], current_values, target_position, damping_factor):
    max_iterations = 1000
    alpha=0.5
    target_position = np.transpose(target_position)
    
    for i in range(max_iterations):
        T = ForwardKinematics(DHArray, current_values)
        n = len(T)-1
        X_A = T[:-1, -1]
        deltaX = target_position - X_A

        Jacobian = JacobianMatrix(DHArray, current_values)
        Jacobian_pos = Jacobian[:n, :]
        dTheta = deltaTheta(Jacobian_pos, deltaX, damping_factor)
        
        current_values = current_values + alpha * dTheta

        T = ForwardKinematics(DHArray, current_values)
        n = len(T)-1
        X_A = T[:-1, -1]
        
        if np.linalg.norm(dTheta) <= 1e-3:
            return current_values
        
        
    return None


class Plotter:
    def _artist_create(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        return wrapper
    
    def __init__(self, _root, projection=None, row=0, column=0, sticky=tk.NSEW, **options):
        self._root = _root
        self.root = tk.PanedWindow(self._root)
        self.root.pack(expand=True, fill=tk.BOTH)

        self.plotter_pane = tk.Frame(self.root)
        menu_frame = tk.Frame(self.plotter_pane)
        menu_frame.pack(side=tk.TOP, expand=False, fill=tk.X)
        
        self.root.add(self.plotter_pane, minsize=100)

        self.menu_button = tk.Menubutton(menu_frame, text="Options",)# relief=tk.RAISED)
        self.menu_button.pack(side=tk.RIGHT)
        
        menu = tk.Menu(self.menu_button, tearoff=0)
        self.menu_button['menu'] = menu
        menu.add_command(label="Edit Lines", command=lambda: self.root.add(self.edit_frame, minsize=100))

        self.edit_frame = tk.Frame(self.root)


        self.fig = Figure(figsize=options.get('figsize', (6, 4)), dpi=options.get('dpi', 100))
        self.ax = self.fig.add_subplot(111, projection = projection)
        self._projection = projection

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plotter_pane)

        if options.get('toolbar', True):
            toolbar_frame = tk.Frame(self.plotter_pane)
            toolbar_frame.pack(side=tk.BOTTOM, expand=False, fill=None)
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            
            toolbar.update()

        self.ax.minorticks_on()
        self.ax.grid(True)
        self.x_label = self.y_label = self.z_label = ''

        self.zmin = self.zmax = self._user_zmin = self._user_zmax = None
        self.lines = {}
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.clear()
        self.label_axis('X (mm)', 'Y (mm)', 'Z (mm)')

        self._set_axis_limit()
        self.canvas.draw()
        self._create_artist_edit_window()

        

        # Copycat functions
        @copy_params(self.ax.scatter)
        def scatter(*args, existing_line=None, **kwargs):
            new_artist = self.ax.scatter(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                new_artist.update_from(existing_line)
                existing_line.remove()
            self._update_artist_selection_widget()
            return new_artist

        @copy_params(self.ax.plot)
        def plot(*args, existing_line=None, **kwargs):
            new_artists = self.ax.plot(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                for artist in new_artists:
                    artist.update_from(existing_line)
                existing_line.remove()
            self._update_artist_selection_widget()
            return new_artists

        @copy_params(self.ax.quiver)
        def quiver(*args, existing_line=None, **kwargs):
            new_artist = self.ax.quiver(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                new_artist.update_from(existing_line)
                existing_line.remove()
            self._update_artist_selection_widget()
            return new_artist
        
        @copy_params(self.ax.vlines)
        def vlines(*args, existing_line=None, **kwargs):
            new_artist = self.ax.vlines(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                new_artist.update_from(existing_line)
                existing_line.remove()
            self._update_artist_selection_widget()
            return new_artist
        
        @copy_params(self.ax.axvline)
        def axvline(*args, existing_line=None, **kwargs):
            new_artist = self.ax.axvline(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                new_artist.update_from(existing_line)
                existing_line.remove()
            self._update_artist_selection_widget()
            return new_artist

        if self._projection == '3d':
            @copy_params(self.ax.add_collection3d)
            def add_collection3d(*args, existing_line=None, **kwargs):
                new_artists = self.ax.add_collection3d(*args, **kwargs)
                if existing_line is not None and existing_line.axes is not None:
                    for artist in new_artists:
                        artist.update_from(existing_line)
                    existing_line.remove()
                self._update_artist_selection_widget()
                return new_artists
            
            self.add_collection3d = add_collection3d
            
        self.scatter = scatter
        self.plot    = plot
        self.quiver  = quiver
        self.grid    = self.ax.grid
        self.legend  = self.ax.legend
        self.vlines  = vlines
        self.axvline = axvline
        self.autoscale_view = self.ax.autoscale_view
   
    def _update(self, keep_axis=True, autoscale=False, change_view=True):
        if change_view:
            if autoscale:
                self.autoscale_view()
            else:
                if keep_axis:
                    self._set_axis_limit(self._user_xmin, self._user_xmax, self._user_ymin, self._user_ymax, self._user_zmin, self._user_zmax)
                else:
                    self._set_axis_limit(self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)
        self.canvas.draw()
        
    update = _update

    def add_menu_option(self, label, command, var=None):
        menu:tk.Menu = self.menu_button.nametowidget(self.menu_button["menu"])
        if not var:
            menu.add_command(label=label, command=command)
        else:
            menu.add_checkbutton(label=label, command=command, variable=var)
            
    def _set_axis_limit(self, xmin=None, xmax=None, ymin=None, ymax=None, zmin=None, zmax=None):
        self.xmin = xmin if xmin is not None else self.ax.get_xlim()[0]
        self.xmax = xmax if xmax is not None else self.ax.get_xlim()[1]
        self.ymin = ymin if ymin is not None else self.ax.get_ylim()[0]
        self.ymax = ymax if ymax is not None else self.ax.get_ylim()[1]

        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_ylim(self.ymin, self.ymax)
        if self._projection == '3d':
            self.zmin = zmin if zmin is not None else self.ax.get_zlim()[0]
            self.zmax = zmax if zmax is not None else self.ax.get_zlim()[1]
            self.ax.set_zlim(self.zmin, self.zmax)
        
    def _focus_view(self, x, y, z, x_dist, y_dist, z_dist):

        xmin = x - x_dist/2
        xmax = x + x_dist/2

        ymin = y - y_dist/2
        ymax = y + y_dist/2

        zmin = None
        zmax = None
        
        if self._projection == '3d':
            zmin = z - z_dist/2
            zmax = z + z_dist/2

        abs_min = min([data for data in (xmin, ymin, zmin) if data is not None])
        abs_max = max([data for data in (xmax, ymax, zmax) if data is not None])

        x_min = xmin if abs(xmax - xmin) >= 1e-3 else  abs_min
        y_min = ymin if abs(ymax - ymin) >= 1e-3 else  abs_min
        if self._projection == '3d':
            z_min = zmin if abs(zmax - zmin) >= 1e-3 else  abs_min

        x_max = xmax if abs(xmax - xmin) >= 1e-3 else abs_max
        y_max = ymax if abs(ymax - ymin) >= 1e-3 else abs_max
        max_ = max(x_max, y_max)
        min_ = min(x_min, y_min)
        if self._projection == '3d':
            z_max = zmax if abs(zmax - zmin) >= 1e-3 else abs_max
            max_ = max(max_, z_max)
            min_ = min(min_, z_min)
        #self._set_axis_limit(x_min, x_max, y_min, y_max, z_min, z_max)
        self._set_axis_limit(min_+x, max_+x, min_+y, max_+y, min_+z, max_+z)
        self.save_user_view()
        self.update(False)

    def save_user_view(self):
        self._user_xmin = self.ax.get_xlim()[0]    
        self._user_xmax = self.ax.get_xlim()[1]    
        self._user_ymin = self.ax.get_ylim()[0]            
        self._user_ymax = self.ax.get_ylim()[1]    
        if self._projection == '3d':               
            self._user_zmin = self.ax.get_zlim()[0]
            self._user_zmax = self.ax.get_zlim()[1]

    def clear(self):
        self.save_user_view()
        self.ax.clear()
        self.label_axis()
        
    def label_axis(self, xlabel=None, ylabel=None, zlabel=None):
        if xlabel is not None:
            self.x_label = xlabel
            
        if ylabel is not None:
            self.y_label = ylabel
        
        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)

        if self._projection == '3d':
            if zlabel is not None:
                self.z_label = zlabel
            self.ax.set_zlabel(self.z_label)

    def plot_robot(self, robot:list[DenavitHartenbergParameter], angles, name='Current Robot Position', color='red', update=True, scatter_line=None, plot_line=None):
        prev_coord= [0.0, 0.0, 0.0]
        T = transformation_matrix(robot[0], angles[0])

        x = []
        y = []
        z = []
        
        current_coord = T[0:3, -1]
        points = [prev_coord, current_coord]
        x.extend([prev_coord[0], current_coord[0]])
        y.extend([prev_coord[1], current_coord[1]])
        z.extend([prev_coord[2], current_coord[2]])
        
        prev_coord = current_coord
        for i, (DH, angle) in enumerate(zip(robot[1:], angles[1:])):
            T = rotate(T, transformation_matrix(DH, angle))
            current_coord = T[0:3, -1]
            points.append(current_coord)

            x.extend([current_coord[0]])
            y.extend([current_coord[1]])
            z.extend([current_coord[2]])

            prev_coord = current_coord

        R = T[:3, :3]

        end_eff_frame_offset = np.array([0, 180, 180])

        rx = Rx(np.deg2rad(end_eff_frame_offset[0]))
        ry = Ry(np.deg2rad(end_eff_frame_offset[1]))
        rz = Rz(np.deg2rad(end_eff_frame_offset[2]))
        R = rotate(R, rx, ry, rz)

        (plot_line, scatter_line, endeff_frame_quiver) = self.lines.get(name, (None, None, None))

        #scatter_line = self.scatter(*zip(*points), color=color, existing_line=scatter_line)
        plot_line = self.plot(x, y, z, color=color, existing_line=plot_line, label=name, marker='.')[0]
        endeff_frame_quiver = self.quiver([x[-1]]*3, [y[-1]]*3, [z[-1]]*3, R[0,:3], R[1,:3], R[2,:3], length=100, existing_line=endeff_frame_quiver, color='red')
        self.lines[name] = (plot_line, scatter_line, endeff_frame_quiver)

        #if update:
        self.update(change_view=False)

        return plot_line, scatter_line

    def plot_shape(self, points, existing_line=None, label='shape'):
        points = [[tuple(point) for point in points],]
        square = Poly3DCollection(points, label=label)
        return self.add_collection3d(square, existing_line=existing_line)

    def plot_path(self, path_name, points, origin=np.array([0.0, 0.0, 0.0]), label='path'):
        x, y, z = [np.array(data) for data in zip(*points)]

        origin_scatter, plot_line = self.lines.get(path_name, (None, None))
        origin_scatter = self.scatter(*origin, existing_line=origin_scatter, label='Origin')
        
        plot_line = self.plot(x, y, z, existing_line=plot_line, marker='.', label=label)[0]

        self.lines[path_name] = (origin_scatter, plot_line)

        xdist = (max(x)-min(x))*2
        ydist = (max(y)-min(y))*2
        zdist = (max(z)-min(z))*2
        
        self._focus_view(*origin, xdist, ydist, zdist)
        self.canvas.draw_idle()

    def display_light_field(self, x1, x2, y1, y2, gantry_angle, collimator_angle, origin=np.array([0,0,0])):

        rotation_matrix =rotate(Rx(np.deg2rad(gantry_angle)), Rz(np.deg2rad(collimator_angle)))
        p1 = rotate_point(np.array([-x1, -y1, 0.0]), rotation_matrix) + origin
        p2 = rotate_point(np.array([x2, -y1, 0.0]) , rotation_matrix) + origin
        p3 = rotate_point(np.array([x2, y2, 0.0])  , rotation_matrix) + origin
        p4 = rotate_point(np.array([-x1, y2, 0.0]) , rotation_matrix) + origin

        light_field_artist = self.lines.get('light field', None)
        
        light_field_artist = self.plot_shape([p1, p2, p3, p4], existing_line=light_field_artist, label='Light Field')

        self.lines['light field'] = light_field_artist

    def _update_options(self, artist):
        artist_type = None
        for type_ in self.artist_options.keys():
            if isinstance(artist, type_):
                artist_type = type_

        if artist is None:
            self.artist_tree.clear()
            self.previous_artist_type = artist_type
            return
        
        if artist_type != self.previous_artist_type:
            self.artist_tree.clear()
            self.artist_tree.add_dict(self.artist_options.get(artist_type, {}))

        self.previous_artist_type = artist_type

        sig = inspect.signature(artist.set)
        for name, param in sig.parameters.items():
            if name in self.artist_options_flat.get(artist_type, {}):
                try:
                    value = getattr(artist, f'get_{name}')()
                except:
                    value = getattr(artist, f'get_face{name}')()

                if 'color' in name:
                    if callable(getattr(artist, f'get_cmap', None)):
                        continue
                    value = mcolors.to_hex(value, keep_alpha=True)

                if name == 'marker':
                    
                    value = Line2D.markers[value]

                while isinstance(value, (tuple, list, np.ndarray)):
                    value = value[-1]

                self.artist_options_flat[artist_type][name].var.set(value)

        self.artist_tree.update()
    
    def _update_lines(self, artist):
        if artist is None:
            return
        artist_type = None
        for type_ in self.artist_options.keys():
            if isinstance(artist, type_):
                artist_type = type_

        sig = inspect.signature(artist.set)
        for name, param in sig.parameters.items():
            if name in self.artist_options_flat.get(artist_type, {}):
                value = self.artist_options_flat[artist_type][name].value
                #if 'color' in name and callable(getattr(artist, f'get_cmap', None)):
                #    continue
                getattr(artist, f'set_{name}')(value)
                #print(name, value)
        self._update_options(artist)
        self.canvas.draw_idle()
                
    def _update_artist_selection_widget(self):
        menu = self.artist_selection_widget['menu']
        menu.delete(0, tk.END)

        artist_keys = list(self.current_artists.keys())

        for artist_name in artist_keys:
            menu.add_command(label=artist_name, command=lambda name=artist_name: (self.artist_var.set(name), self._update_options(self.current_artists.get(self.artist_var.get(), None))   ))

        if artist_keys and self.artist_var.get() not in artist_keys:
            self.artist_var.set(artist_keys[0])
            
        elif not artist_keys:
            self.artist_var.set('')
        
        #self.artist_tree.add_dict(self.artist_options[self.previous_artist_type])
        self._update_options(self.current_artists.get(self.artist_var.get(), None))       

    @property
    def current_artists(self):
        return {artist.get_label(): artist for artist in self.ax.get_lines() + self.ax.collections}

    def _create_artist_edit_window(self):

        self.edit_frame.columnconfigure(0, weight=1)

        selection_frame = tk.Frame(self.edit_frame)
        selection_frame.pack(side=tk.TOP, fill=tk.X)
        selection_frame.columnconfigure(0, weight=1)

        self.artist_var = tk.StringVar()
        
        tk.Button(selection_frame, text='Close', command=lambda: self.root.remove(self.edit_frame)).grid(row=0, column=1, sticky=tk.E)

        markers = {name:value for value, name in Line2D.markers.items()}

        

        self.update_command = lambda e=None: self._update_lines(self.current_artists.get(self.artist_var.get(), None))

        quick_scale = lambda name, from_=0.0, to=1.0, default=1.0, command=self.update_command: TreeInput(name, tk.DoubleVar(value=default), tk.Scale, orient=tk.HORIZONTAL, showvalue=False, width=15, resolution=0.01, from_=from_, to=to, command=command)
        self.artist_options = {
            Line2D: {
                'alpha'     : quick_scale('Alpha'),
                'color'     : TreeInput('Color', tk.StringVar(value="#FF0000"), lambda *args, **kwargs: colorchooser.askcolor(*args, **kwargs, title='Choose Color')[-1]),
                'linestyle' : TreeInput('Line Style', tk.StringVar(value=''), tk.OptionMenu, '', *('-', '--', '-.', ':', ''), command=self.update_command),
                'linewidth' : quick_scale('Line Width', to=10.0),
                
                
                'markers': {
                    'marker'              : TreeInput('Marker', tk.StringVar(value='point'), tk.OptionMenu, 'point', *markers.values(), command=self.update_command, value_lookup=markers),
                    'markersize'          : quick_scale('Marker Size', to=10.0),
                    'markeredgecolor'     : TreeInput('Marker Edge Color', tk.StringVar(value="#FF0000"), lambda *args, **kwargs: colorchooser.askcolor(*args, **kwargs, title='Choose Color')[-1]),
                    'markerfacecolor'     : TreeInput('Marker Face Color', tk.StringVar(value="#FF0000"), lambda *args, **kwargs: colorchooser.askcolor(*args, **kwargs, title='Choose Color')[-1]),
                    'markerfacecoloralt'  : TreeInput('Marker Face Color Alt', tk.StringVar(value="#FF0000"), lambda *args, **kwargs: colorchooser.askcolor(*args, **kwargs, title='Choose Color')[-1]),
                },
            },
            Line3DCollection: {
                'alpha'     : quick_scale('Alpha'),
                'color'     : TreeInput('Color', tk.StringVar(value="#FF0000"), lambda *args, **kwargs: colorchooser.askcolor(*args, **kwargs, title='Choose Color')[-1]),
                'linewidth' : quick_scale('Line Width', to=10.0),
            },
        }

        self.artist_options[Line3D] = self.artist_options[Line2D]
        self.artist_options[PathCollection] = self.artist_options[Line3DCollection]
        self.artist_options_flat = {}
        for type_, items in self.artist_options.items():
            self.artist_options_flat[type_] = flatten_dict(items)
        
        self.artist_selection_widget = ttk.OptionMenu(selection_frame, self.artist_var, self.artist_var.get(), *list(self.current_artists.keys()), command=lambda e=None: self._update_options(self.current_artists.get(self.artist_var.get(), None)))
        self.artist_selection_widget.grid(row=0, column=0, sticky=tk.EW)

        headers = ['Values',]
        self.artist_tree = LineEditTree(self.edit_frame, columns=headers, show='tree headings')

        self.artist_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.artist_tree.column("#0", minwidth=50)
        for i, header in enumerate(headers):
            self.artist_tree.heading(header, text=header)
            self.artist_tree.column(i, width=75, minwidth=75)

        self.previous_artist_type = None
        self.artist_tree.add_apply_function(self.update_command)

class TreeInput(object):
    def __init__(self, name, var:tk.Variable, widget_type:tk.Widget, *args, value_lookup=None, **kwargs):
        self.name = name
        self.var = var
        self.widget_type = widget_type
        self.value_lookup = value_lookup if value_lookup is not None else {}
        self._args = args
        self._kwargs = kwargs
        self.enable = True

        if self.widget_type is tk.OptionMenu:
            self._args = self.var, *self._args

    @property
    def value(self):
        try:
            value = self.var.get()
            return self.value_lookup.get(value, value)
        except BaseException as e:
            return None

    def get_widget(self, root):
        if not inspect.isclass(self.widget_type) or not issubclass(self.widget_type, tk.BaseWidget):
            return lambda: self.widget_type(*self._args, **self._kwargs)

        self.widget = self.widget_type(root, *self._args, **self._kwargs)
        
        for name in self.widget.keys():
            if 'variable' in name.lower():
                self.widget.configure({name: self.var})
                break

        if isinstance(self.widget_type, tk.Entry):
            self.widget.icursor(tk.END)
            self.widget.select_range(0, tk.END)

        return self.widget

class LineEditTree(ttk.Treeview):
    def __init__(self, *args, **kwargs):
        ttk.Treeview.__init__(self, *args, **kwargs)
        self.bind("<Double-1>", self.on_double_click)
        self.vars:dict[str, tuple[str, TreeInput]] = {}
        self.active_widget = None
        self.apply_func = None
        self.tag_configure("normal", foreground="black")
        self.tag_configure("disbale", foreground="gray")
    
    def add_dict(self, data:dict[str, tuple[str, TreeInput]], current_id=''):
        for name, value in data.items():

            if isinstance(value, dict):
                new_id = self.insert(current_id, tk.END, text=name, open=True)
                self.add_dict(value, new_id)
                #self.vars[id_] = (name, value)
            else:
                id_ = self.insert(current_id, tk.END, text=value.name, values=[value.value,], open=True)
                self.vars[id_] = (name, value)

    def update(self):
        for row_id, (name, value) in self.vars.items():
            self.apply_changes(row_id, 0, value.value, False)

    def clear(self):
        if self.active_widget is not None:
            try:
                self.active_widget.destroy()
            except:
                pass
            self.active_widget = None
        self.vars = {}
        self.delete(*self.get_children())

    def on_double_click(self, event):
        # Identify the exact region clicked
        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return

        # Find the row ID and column name
        row_id = self.identify_row(event.y)
        column = self.identify_column(event.x)

        if row_id not in self.vars:
            return
        
        (name, value) = self.vars[row_id]
        
        # Determine numerical column index (e.g., '#1' -> 0)
        col_index = int(column.replace("#", "")) - 1

        # Get bounding box coordinates of the targeted cell
        x, y, width, height = self.bbox(row_id, column)

        if col_index >= len(self.item(row_id, "values")):
            return
    
        # Create and overlay the temporary Entry widget

        widget = value.get_widget(self)
        if not isinstance(widget, tk.BaseWidget):
            return_value = widget()
            if return_value:
                value.var.set(return_value)
                self.apply_changes(row_id, col_index, return_value)
            
            return return_value
        
        widget.place(x=x, y=y, width=width, height=height)
        self.active_widget = widget
        widget.focus()
        

        # Inner function to save the new value
        def save_edit(widget, event_obj:tk.Event=None, var:tk.Variable=None):
            if isinstance(widget, tk.OptionMenu):
                new_val = var.get()
            else:
                new_val = widget.get()
                if var:
                    var.set(new_val)
                    
            self.apply_changes(row_id, col_index, new_val)

            # Skip deleting widget if user scrolls on a combobox 
            #if isinstance(widget, ttk.Combobox) and str(event_obj.type) == '35':
            #    return
            
            widget.destroy()
            self.unbind("<MouseWheel>")
            self.unbind("<Configure>")
            

        def reposition(widget:tk.Widget):
            widget.place_forget()

            if self.bbox(row_id, column):
                x, y, width, height = self.bbox(row_id, column)
                widget.place(x=x, y=y, width=width, height=height)
                widget.focus()

        def _on_focus_out(widget, input_):
            row_values = list(self.item(row_id, "values"))

            # Update the specific column value
            input_.var.set(row_values[col_index]) 

            widget.destroy()
            self.unbind("<MouseWheel>")
            self.unbind("<Configure>")

        
        # Bind lifecycle events to the temporary widget
        self.bind("<MouseWheel>", lambda *args: self.after('idle', reposition, widget))
        self.bind("<Configure>", lambda *args: self.after('idle', reposition, widget))
        widget.bind("<Return>", lambda e: save_edit(widget, e, value.var))
        widget.bind("<FocusOut>", lambda e: _on_focus_out(widget, value))

    def apply_changes(self, row_id, col_index, new_value, run_function=True):
        # Fetch all current values for this row
        row_values = list(self.item(row_id, "values"))
        # Update the specific column value
        row_values[col_index] = new_value

        # Apply changes back to the tree row
        self.item(row_id, values=row_values)

        if run_function and callable(self.apply_func):
            self.apply_func()

    def add_apply_function(self, func):
        self.apply_func = func
        
def flatten_dict(obj:dict,):
    return_dict = {}
    for key, value in obj.items():
        if isinstance(value, dict):
            return_dict |= flatten_dict(value)
        else:
            return_dict[key] = value
    return return_dict
