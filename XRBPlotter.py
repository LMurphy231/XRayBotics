import dataclasses
import logging
import os
import tkinter as tk

import numpy as np
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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

    A = rotate(Rz(DH.theta+DH.set_angle),Rx(DH.alpha))
    B = np.array([[
        DH.a*np.cos(DH.theta + DH.set_angle),
        DH.a*np.sin(DH.theta + DH.set_angle),
        DH.d
        ]]).T
    C = np.array([[0,0,0]])
    D = np.array([[1]]) 
    return np.block([
            [A,B], 
            [C,D]
           ])





class Plotter:
    def __init__(self, root, **options):
        self.root = root
        self.fig = Figure(figsize=options.get('figsize', (6, 4)), dpi=options.get('dpi', 100))
        self.ax = self.fig.add_subplot(111, projection=options.get('projection', None))
        self._projection = options.get('projection', None)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        if options.get('toolbar', True):
            toolbar_frame = tk.Frame(self.root)
            toolbar_frame.grid(row=1, column=0, sticky=tk.W)
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            toolbar.update()

        self.ax.minorticks_on()
        self.ax.grid(True)
        self.x_label = self.y_label = self.z_label = ''

        self.zmin = self.zmax = self._user_zmin = self._user_zmax = 0
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky=tk.NSEW)
        self.clear()
        self.label_axis('X (mm)', 'Y (mm)', 'Z (mm)')
        self._set_axis_limit(-500, 500, -500, 500, -500, 500)
        self.canvas.draw()

        # Copycat functions
        self.scatter = self.ax.scatter
        self.plot    = self.ax.plot

    def _update(self, keep_axis=True):
        if keep_axis:
            self._set_axis_limit(self._user_xmin, self._user_xmax, self._user_ymin, self._user_ymax, self._user_zmin, self._user_zmax)
        else:
            self._set_axis_limit(self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax)
        self.canvas.draw()

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

    
    def clear(self):
        self._user_xmin = self.ax.get_xlim()[0]
        self._user_xmax = self.ax.get_xlim()[1]
        self._user_ymin = self.ax.get_ylim()[0]
        self._user_ymax = self.ax.get_ylim()[1]
        if self._projection == '3d':
            self._user_zmin = self.ax.get_zlim()[0]
            self._user_zmax = self.ax.get_zlim()[1]
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

    def plot_robot(self, angles, color='red'):
        plotter.clear()

        prev_coord= [0.0, 0.0, 0.0]
        T = transformation_matrix(FR5Joints[0], angles[0])
        current_coord = T[0:3, -1]
        self.scatter(*prev_coord)
        self.scatter(*current_coord)
        self.plot([current_coord[0], prev_coord[0]], [current_coord[1], prev_coord[1]], [current_coord[2], prev_coord[2]], color=color)
        prev_coord = current_coord
        for i, (DH, angle) in enumerate(zip(FR5Joints[1:], angles[1:])):
            T = rotate(T, transformation_matrix(DH, angle))
            current_coord = T[0:3, -1]
            self.scatter(*current_coord)
            plotter.plot([current_coord[0], prev_coord[0]], [current_coord[1], prev_coord[1]], [current_coord[2], prev_coord[2]], color=color)
            prev_coord = current_coord

        self._update()

    def plot_shape(self, points):
        points = [[tuple(point) for point in points],]
        square = Poly3DCollection(points)
        self.ax.add_collection3d(square)

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



