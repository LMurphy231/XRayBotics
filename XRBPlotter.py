import dataclasses
import logging
import os
import tkinter as tk
from functools import wraps
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

P = ParamSpec("P")
R = TypeVar("R")

def copy_params(source: Callable[P, Any]) -> Callable[[Callable[..., R]], Callable[P, R]]:
    def decorator(target: Callable[..., R]) -> Callable[P, R]:
        return target
    return decorator

global Rz
global Ry
global Rx

Rz = lambda angle: np.array([
    [np.cos(angle), -np.sin(angle), 0],
    [np.sin(angle),  np.cos(angle), 0],
    [0          ,  0          , 1],
])
Ry = lambda angle: np.array([
    [np.cos(angle)  ,   0 , np.sin(angle)],
    [0              ,   1 , 0          ],
    [-np.sin(angle) ,   0 , np.cos(angle)],
])
Rx = lambda angle: np.array([
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

class Plotter:
    def _artist_create(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)
        return wrapper
    
    def __init__(self, _root, projection=None, row=0, column=0, sticky=tk.NSEW, **options):
        self._root = _root
        self.root = tk.Frame(self._root)
        self.root.pack(expand=True, fill=tk.BOTH)

        self.fig = Figure(figsize=options.get('figsize', (6, 4)), dpi=options.get('dpi', 100))
        self.ax = self.fig.add_subplot(111, projection = projection)
        self._projection = projection

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        if options.get('toolbar', True):
            toolbar_frame = tk.Frame(self.root)
            #toolbar_frame.grid(row=1, column=0, sticky=tk.W)
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
        #self._set_axis_limit(-500, 500, -500, 500, -500, 500)
        self._set_axis_limit()
        self.canvas.draw()

        # Copycat functions
        @copy_params(self.ax.scatter)
        def scatter(*args, existing_line=None, **kwargs):
            new_artist = self.ax.scatter(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                new_artist.update_from(existing_line)
                existing_line.remove()
            return new_artist

        @copy_params(self.ax.plot)
        def plot(*args, existing_line=None, **kwargs):
            new_artists = self.ax.plot(*args, **kwargs)
            if existing_line is not None and existing_line.axes is not None:
                for artist in new_artists:
                    artist.update_from(existing_line)
                existing_line.remove()
            return new_artists

        if self._projection == '3d':
            @copy_params(self.ax.add_collection3d)
            def add_collection3d(*args, existing_line=None, **kwargs):
                new_artist = self.ax.add_collection3d(*args, **kwargs)
                if existing_line is not None and existing_line.axes is not None:
                    new_artist.update_from(existing_line)
                    existing_line.remove()
                return new_artist
            
            self.add_collection3d = add_collection3d
            
        self.scatter = scatter
        self.plot    = plot
        self.grid    = self.ax.grid
        self.legend  = self.ax.legend
        self.autoscale_view = self.ax.autoscale_view
   


    def _update(self, keep_axis=True, autoscale=False):
        if autoscale:
            self.autoscale_view()
        else:
            if keep_axis:
                self._set_axis_limit(self._user_xmin, self._user_xmax, self._user_ymin, self._user_ymax, self._user_zmin, self._user_zmax)
            else:
                self._set_axis_limit(self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)
        self.canvas.draw()
        
    update = _update

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

    def plot_robot(self, robot:list[DenavitHartenbergParameter], angles, color='red', clear=True, update=True, scatter_line=None, plot_line=None):
        if clear:
            self.clear()

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


        (plot_line, scatter_line) = self.lines.get('robot', (None, None))

        scatter_line = self.scatter(*zip(*points), color=color, existing_line=scatter_line)
        plot_line = self.plot(x, y, z, color=color, existing_line=plot_line)[0]

        self.lines['robot'] = (plot_line, scatter_line)
        
        if update:
            self.update()

        return plot_line, scatter_line

    def plot_shape(self, points, existing_line=None):
        points = [[tuple(point) for point in points],]
        square = Poly3DCollection(points)
        return self.add_collection3d(square, existing_line=existing_line)

    def plot_path(self, path_name, points, origin=np.array([0.0, 0.0, 0.0])):
        x, y, z = [np.array(data) for data in zip(*points)]

        origin_scatter, plot_line, scatter_line = self.lines.get(path_name, (None, None, None))
        origin_scatter = self.scatter(*origin, existing_line=origin_scatter)
        
        plot_line = self.plot(x, y, z, existing_line=plot_line)[0]

        scatter_line = self.scatter(x, y, z, existing_line=scatter_line)

        self.lines[path_name] = (origin_scatter, plot_line, scatter_line)

        xdist = (max(x)-min(x))*2
        ydist = (max(y)-min(y))*2
        zdist = (max(z)-min(z))*2
        
        self._focus_view(*origin, xdist, ydist, zdist)
        self.canvas.draw_idle()

    
        
    #def _artist_create(self, artist, creation_function, *args, **kwargs):

    def display_light_field(self, x1, x2, y1, y2, gantry_angle, collimator_angle, origin=np.array([0,0,0])):

        rotation_matrix =rotate(Rx(np.deg2rad(gantry_angle)), Rz(np.deg2rad(collimator_angle)))
        p1 = rotate_point(np.array([-x1, -y1, 0.0]), rotation_matrix) + origin
        p2 = rotate_point(np.array([x2, -y1, 0.0]) , rotation_matrix) + origin
        p3 = rotate_point(np.array([x2, y2, 0.0])  , rotation_matrix) + origin
        p4 = rotate_point(np.array([-x1, y2, 0.0]) , rotation_matrix) + origin

        light_field_artist = self.lines.get('light field', None)
        
        light_field_artist = self.plot_shape([p1, p2, p3, p4], existing_line=light_field_artist)

        self.lines['light field'] = light_field_artist



        
if __name__ == '__main__':
    root = tk.Tk()
    entry_frame = tk.Frame(root)
    entry_frame.grid(row=0, column=0,sticky=tk.NSEW)
    plotter_frame = tk.Frame(root)
    plotter_frame.grid(row=0, column=1,sticky=tk.NSEW)
    plotter = Plotter(plotter_frame, projection='3d')

    vars = []
    for i in range(6):
        var = tk.DoubleVar(value=0.0)
        vars.append(var)
        
        var.trace_add('write', lambda *args: plotter.plot_robot([var.get()*np.pi/180 if var.get() else 0.0 for var in vars]))
        tk.Label(entry_frame, text=f'Joint {i}: ').grid(row=i, column=0, sticky=tk.E)
        tk.Entry(entry_frame, textvariable=var).grid(row=i, column=1, sticky=tk.NSEW)
    tk.Button(entry_frame, text='plot', command=lambda: plotter.plot_robot([var.get()*np.pi/180 if var.get() else 0.0 for var in vars])).grid(row=6, column=0)

    plotter.plot_robot([var.get()*np.pi/180 for var in vars])
    root.mainloop()



