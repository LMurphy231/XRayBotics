from dataclasses import dataclass
from collections import UserDict
from typing import Union
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D 


import numpy


@dataclass
class Coordinate:
    x: float
    y: float
    z: float
    def __str__(self):
        return f'x: {self.x:>5.4g}, y: {self.y:>5.4g}, z: {self.z:>5.4g}'
    
    def get(self):
        return self.x, self.y, self.z
    
@dataclass 
class Position:
    local: Coordinate
    
    
@dataclass
class Limit:
    min: float
    max: float

@dataclass
class AngleLimit:
    theta: Union[Limit, None]
    phi  : Union[Limit, None]

@dataclass
class Direction:
    theta: float
    phi  : float
    def __str__ (self):
        return f'Theta: {self.theta}, Phi: {self.phi}'
    
@dataclass 
class TerminalPoint:
    coord  : Coordinate
    tangent: Direction
    name: Union[str, None] = None
    def __str__(self):
        return f'{self.coord} at {self.tangent}'


class BboxCorners(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def __setitem__(self, keys, value):
        path = self.data
        if not isinstance(keys, (tuple, list)):
            keys = (keys, )
        for i, key in enumerate(keys):
            if key not in path:
                path[key] = {}
            if i == len(keys)-1:
                path[key] = value
            path = path[key]
    
    def __getitem__(self, keys):
        path = self.data
        for key in keys:
            if key not in path:
                raise KeyError(f'No index "{key}" found...')
            path = path[key]
        return path
        
    def __iter__(self):
        def get_items(current_keys=[], path={}, data_list=[]):
            if not isinstance(path, dict):
                data_list.append((tuple(current_keys), path))
                return
            
            for key in path:
                next_keys = current_keys + [key]
                get_items(next_keys, path[key], data_list)
            return data_list
        
        items = get_items(path = self.data)
        for keys, data in items:
            yield keys, data 
    
class Bbox:
    def __init__(self, l: float, w: float, h: float, main_terminal_point: Coordinate, sub_terminal_points: Union[tuple[Coordinate], list[Coordinate]] = ()):
        self.l = l
        self.w = w
        self.h = h
        self.main_terminal_point = main_terminal_point
        if not isinstance(sub_terminal_points, (tuple, list)):
            sub_terminal_points = tuple((sub_terminal_points, ))
        self.sub_terminal_points = sub_terminal_points
        
        self._setup()
        self.shape = self._get_shape()
    
    def _setup(self):
        self.corner = BboxCorners()
        coord =  self.main_terminal_point
        for z in range(2):
            for y in range(2):
                for x in range(2):
                    cx = (x*self.l - coord.x)
                    cy = (y*self.w - coord.y)
                    cz = (z*self.h - coord.z)
                    self.corner[x, y, z] = Coordinate(cx, cy, cz)
    def __str__(self):
        item_name = f'Main Terminal:\n{self.main_terminal_point}\n\nWith corners:\n'
        for key, coordinate in self.corner:
            item_name += f'{key} = {coordinate}\n'
        return item_name


    def _get_shape(self):
        def _flip_bit(key):
            return 1 if key == 0 else 0
        
        lines = []
        points = []
        data = {}
        for keys, coordinate in self.corner:
            point = (coordinate.x, coordinate.y, coordinate.z)
            points.append(point)
            data[keys] = point
        used_keys = []
        for keys in data:
            for i, key in enumerate(keys):
                key_pair = list(keys[:])
                key_pair[i] = _flip_bit(key)
                if key_pair in used_keys:
                    continue
                x1, y1, z1 = data[keys]
                x2, y2, z2 = data[tuple(key_pair)]
                x = numpy.linspace(x1, x2, 2)
                y = numpy.linspace(y1, y2, 2)
                z = numpy.linspace(z1, z2, 2)
                
                lines.append((x, y, z))

            used_keys.append(list(keys))
            

        return points, lines


@dataclass 
class Terminal:
    position : Coordinate
    normal   : Direction
    angle_lim: Limit
    parent   : Bbox
    child    : Bbox

def _rotatex(x, y, z, angle):
    if numpy.isnan(angle):
        return x, y, z
    nx = x
    ny = y * numpy.cos(angle) - z * numpy.sin(angle)
    nz = y * numpy.sin(angle) + z * numpy.cos(angle)
    return nx, ny, nz

def _rotatey(x, y, z, angle):
    if numpy.isnan(angle):
        return x, y, z
    nx = x * numpy.cos(angle) + z * numpy.sin(angle)
    ny = y
    nz = -x * numpy.sin(angle) + z * numpy.cos(angle)
    return nx, ny, nz

def _rotatez(x, y, z, angle):
    if numpy.isnan(angle):
        return x, y, z
    nx = x * numpy.cos(angle) - y * numpy.sin(angle)
    ny = x * numpy.sin(angle) + y * numpy.cos(angle)
    nz = z
    return nx, ny, nz

def _rotatexyz(x, y, z, theta, phi):   
    nx, ny, nz = _rotatey(x, y, z, phi)
    nx, ny, nz = _rotatez(nx, ny, nz, theta)
    return nx, ny, nz


def _get_radius(x, y, z):
    return numpy.sqrt(x**1 + y**2 + z**2)







def plot_terminal(ax, terminal: Terminal):
    pos = terminal.position
    norm = terminal.normal

    parent = terminal.parent
    child = terminal.child
    
    plot_bbox(ax, parent, dx=pos.x, dy=pos.y, dz=pos.z, terminal_color='red')
    plot_bbox(ax, child, theta=norm.theta, phi=norm.phi, dx=pos.x, dy=pos.y, dz=pos.z)

def plot_bbox(ax: plt.Axes, bbox: Bbox, theta=0.0, phi=numpy.pi/2, dx=0.0, dy=0.0, dz=0.0, pointcolor='purple', linecolor= 'green', terminal_color='orange'):
    points, lines = bbox.shape
    terminal_coord = bbox.main_terminal_point

    # Create the plot
    for x, y, z in points: 
        nx, ny, nz = _rotatexyz(x, y, z, theta, phi)
        ax.scatter(nx, ny, nz, c=pointcolor) # 'c' sets the color based on 'z' values


    x1, y1, z1 = points[0]
    nx, ny, nz = _rotatexyz(x1 + terminal_coord.x, y1 + terminal_coord.y, z1 + terminal_coord.z, theta, phi)
    ax.scatter(nx, ny, nz, c=terminal_color, marker='+') # 'c' sets the color based on 'z' values
    
    for terminal in bbox.sub_terminal_points:
        x1, y1, z1 = points[0]
        nx, ny, nz = _rotatexyz(x1 + terminal.x, y1 + terminal.y, z1 + terminal.z, theta, phi)
        ax.scatter(nx, ny, nz, c=terminal_color, marker='+') # 'c' sets the color based on 'z' values

    # Set labels
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    for x, y, z in lines:
        # Create the plot
        nx, ny, nz = _rotatexyz(x, y, z, theta, phi)
        ax.plot(nx, ny, nz, color=linecolor)

    # Set labels
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    







class LineGraphApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Line Graph")
        self.root.bind('<Destroy>', self._quit)
        

        tk.Scale(root, resolution=0.1, label='Phi',   from_=-numpy.pi/2, to=numpy.pi/2, command=lambda e: self.update_plot(phi=e)).pack(side='left')
        tk.Scale(root, resolution=0.1, label='Theta', from_=-numpy.pi,   to=numpy.pi,   command=lambda e: self.update_plot(theta=e)).pack(side='left')



        connection_point = Coordinate(1, 1, 1)
        connection_direction = Direction(numpy.pi/3, 0)
        angle_limits = AngleLimit(Limit(-numpy.pi, numpy.pi), Limit(0, 0))
        
        bbox = Bbox(5, 2, 1, Coordinate(.5, .5, 0))
        bbox1 = Bbox(1, 1, 3, Coordinate(.5, .5, 0), Coordinate(.5, 1, 2.5))
        self.terminal = Terminal(connection_point, connection_direction, angle_limits, bbox, bbox1)


        fig = plt.figure()
        self.ax = fig.add_subplot(projection='3d')
        
        self.canvas = FigureCanvasTkAgg(fig, master=root)
        toolbar = NavigationToolbar2Tk(self.canvas, root)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)


        self.update_plot()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def _quit(self, *args):
        self.root.quit()     # stops mainloop

        
    def update_plot(self, theta=None, phi=None):
        if theta is not None: 
            self.terminal.normal.theta = float(theta)
        if phi is not None: 
            self.terminal.normal.phi = float(phi)
        self.ax.clear()

        plot_terminal(self.ax, self.terminal)

        self.ax.scatter(-6, -6, -6, marker='+') # 'c' sets the color based on 'z' values
        self.ax.scatter(6, 6, 6, marker='+') # 'c' sets the color based on 'z' values

        self.canvas.draw()
        
        




if __name__ == "__main__":
    
    #plot_bbox(ax, bbox1)
    
    root = tk.Tk()
    app = LineGraphApp(root)
    root.mainloop()

    