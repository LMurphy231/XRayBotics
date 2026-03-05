import dataclasses 
from collections import UserDict
from typing import Union
import tkinter as tk
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D 

import numpy

@dataclasses.dataclass()
class Coordinate:
    x: Union[float, int]
    y: Union[float, int]
    z: Union[float, int]

    @property
    def radius(self):
        return Radius(_radius(self))
    
    @property
    def angle(self):
        return _angle(self)

    def __add__(self, other):
        if isinstance(other, (Coordinate)):
            return Coordinate(self.x+other.x, self.y+other.y, self.z+other.z)
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iadd__(self, other):
        if isinstance(other, (Coordinate)):
            self.x += other.x
            self.y += other.y
            self.z += other.z
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        if isinstance(other, (Coordinate)):
            return Coordinate(self.x-other.x, self.y-other.y, self.z-other.z)
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __isub__(self, other):
        if isinstance(other, (Coordinate)):
            self.x -= other.x
            self.y -= other.y
            self.z -= other.z
            return self
        raise TypeError(f"unsupported operand type(s) for -=: '{type(self).__name__}' and '{type(other).__name__}'")
        
    def __mul__(self, other):
        if isinstance(other, Coordinate):
            return self.x*other.x + self.y*other.y + self.z*other.z
        if isinstance(other, Angle):
            return rotate(self,other)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __imul__(self, other):
        if isinstance(other, Angle):
            self.x, self.y, self.z = self.radius *other
            return self
        raise TypeError(f"unsupported operand type(s) for *=: '{type(self).__name__}' and '{type(other).__name__}'")

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __str__(self):
        return f'x: {self.x:>5.4g}, y: {self.y:>5.4g}, z: {self.z:>5.4g}'

@dataclasses.dataclass()
class Angle:
    theta: float=0
    phi  : float=numpy.pi/2

    def __add__(self, other):
        if isinstance(other, Angle):
            return Angle(self.theta+other.theta, self.phi+other.phi)
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iadd__(self, other):
        if isinstance(other, Angle):
            self.theta += other.theta
            self.phi   += other.phi
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        if isinstance(other, Angle):
            return Angle(self.theta-other.theta, self.phi-other.phi)
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __isub__(self, other):
        if isinstance(other, Angle):
            self.theta -= other.theta
            self.phi   -= other.phi
            return self
        raise TypeError(f"unsupported operand type(s) for -=: '{type(self).__name__}' and '{type(other).__name__}'")

    def __mult__(self, other):
        if isinstance(other, Coordinate):
            return rotate(other, self)
        if isinstance(other, Radius):
            return _spherical(other.r, self.theta, self.phi)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")



@dataclasses.dataclass()
class Radius:
    r: Union[float, int]

    def __mul__(self, other):
        if isinstance(other, Angle):
            return _spherical(self.r, other.theta, other.phi)
        if isinstance(other, (int, float)):
            return Radius(self.r*other)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")




@dataclasses.dataclass(frozen=True)
class Dimension:
    l: Union[float, int]
    w: Union[float, int]
    h: Union[float, int]

@dataclasses.dataclass
class Limit:
    min: Union[float, int]
    max: Union[float, int]
    tolerance: float = 1e-3

    def __contains__(self, other):
        if isinstance(other, (float, int)):
            return other >= self.min * (1 - self.tolerance) and other <= self.max * (1 + self.tolerance)
        raise TypeError(f"unsupported operand type(s) for contains: '{type(self).__name__}' and '{type(other).__name__}'")

    def __str__(self):
        return f'[{self.min}, {self.max}]'


class AngleLimit:
    def __init__(self, theta: Limit=Limit(0, 0), phi:Limit=Limit(numpy.pi/2, numpy.pi/2), tolerance=1e-3):
        self.theta = theta
        self.phi   = phi  
        self.theta.tolerance = tolerance
        self.phi.tolerance   = tolerance
        self.tolerance = tolerance

    def __contains__(self, item):
        if isinstance(item, Angle):
            if item.theta not in self.theta:
                return False
            if item.phi not in self.phi:
                return False
            return True
        raise TypeError(f"Item type '{type(item).__name__}' must be an Angle")
    
    def __iter__(self):
        yield self.theta
        yield self.phi

    def __str__(self):
        return f'Theta: {self.theta} Phi: {self.phi}'
    
class Line:
    def __init__(self, pos1: Coordinate, pos2:Coordinate):
        self.pos1 = pos1
        self.pos2 = pos2
        self.radius = _radius(pos1, pos2)

    def __add__(self, other):
        if isinstance(other, Coordinate):
            return Line(self.pos1+other, self.pos2+other)
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iadd__(self, other):
        if isinstance(other, Coordinate):
            self.pos1 += other 
            self.pos2 += other
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        if isinstance(other, Coordinate):
            return Line(self.pos1-other, self.pos2-other)
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __isub__(self, other):
        if isinstance(other, Coordinate):
            self.pos1 -= other 
            self.pos2 -= other
            return self
        raise TypeError(f"unsupported operand type(s) for -=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __mul__(self, other):
        if isinstance(other, (float, int, Angle)):
            return Line(self.pos1 * other, self.pos2 * other)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

    def __imul__(self, other):
        if isinstance(other, Angle):
            self.pos1 *= other
            self.pos2 *= other
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iter__(self):
        return (axis for axis in [*zip(self.pos1, self.pos2)])
    
    def _radius(self):
        return _radius(self.pos1, self.pos2)
    
    def _plot(self, ax: plt.Axes):
        ax.plot(*self.__iter__(), c='blue')

class Position:
    def __init__(self, base: Coordinate, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None): 
        self.base = base
        self.local: Coordinate
        self.glob : Coordinate
        self.cur_angle = set_angle if isinstance(set_angle, Angle) else Angle(0,numpy.pi/2)
        self.parent_angle = parent_angle if isinstance(parent_angle, Angle) else Angle(0,numpy.pi/2)
        self._update(set_angle, offset, parent_angle)
    
    def __str__(self):
        return f'Base:   {self.base}\nLocal:  {self.local}\nGloabl: {self.glob}'
    
    def _update(self, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None):
        if isinstance(set_angle, Angle):
            self.cur_angle = set_angle
        if isinstance(parent_angle, Angle):
            self.parent_angle = parent_angle

        # Update current angle and get new local coordinate based on that angle
        self.local = self.base * self.cur_angle
         
        # Update Global position
        self.glob = offset + self.base * (self.parent_angle  + self.cur_angle)
    
    @property
    def base_angle(self):
        return _angle(self.base)

class Segment:
    def __init__(self, dim: Dimension, end_terminal: Coordinate, main_terminal: Coordinate=Coordinate(0.0,0.0,0.0), set_angle: Angle=None, 
                 offset: Coordinate=Coordinate(0.0,0.0,0.0), parent_angle: Angle=None, path: tuple[Coordinate]=()):
        self.dim = dim
        self.end_terminal = Position(end_terminal, set_angle, offset, parent_angle)
        self.main_terminal = Position(main_terminal, set_angle, offset, parent_angle)
        self.set_angle = set_angle
        self.offset = offset
        if not isinstance(path, tuple):
            path = (path, )
        self.path = self._set_path(path)
    
    def _update(self, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None):
        self.main_terminal._update(set_angle, offset, parent_angle)
        self.end_terminal._update(set_angle, offset, parent_angle)
        
        for point in self.path:
            point._update(set_angle, offset, parent_angle)
        print((_angle(self.end_terminal.glob, self.main_terminal.glob), self.end_terminal.cur_angle))

    def _set_path(self, set_path: tuple[Coordinate]=()) -> tuple[Position]: 
        path = []
        if set_path is None:
            x1, y1, z1 = self.main_terminal.base
            x2, y2, z2 = self.end_terminal.base
            if z1 != z2:
                path.append(Position(Coordinate(x1, y1, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
            if y1 != y2:
                path.append(Position(Coordinate(x1, y2, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
            if x1 != x2:
                path.append(Position(Coordinate(x2, y2, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
        else:
            for coord in set_path:
                path.append(Position(coord, self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
        return tuple(path)

    def _get_lines(self) -> tuple[Line]:
        lines = []
        prev_pos = self.main_terminal
        for pos in self.path:
            lines.append(Line(prev_pos.glob, pos.glob))
            prev_pos = pos
        lines.append(Line(prev_pos.glob, self.end_terminal.glob))
        return tuple(lines)

    def _plot(self, ax: plt.Axes, annotate=False, color='red'):
        ax.scatter(*(self.end_terminal.glob), marker='+', c=color)
        ax.scatter(*(self.main_terminal.glob), marker='o')
        if annotate:
            ax.text(*self.end_terminal.glob, s=f'{self.end_terminal.glob}')
        lines = self._get_lines()
        for line in lines:
            line._plot(ax)
            

    @property
    def base_angle(self):
        return _angle(self.end_terminal.base, self.main_terminal.base)
       
    @property
    def local_angle(self):
        return _angle(self.end_terminal.local, self.main_terminal.local)

    @property
    def global_angle(self):
        return _angle(self.end_terminal.glob, self.main_terminal.glob)

class Joint:
    def __init__(self, id_, parent: Segment, child: Segment, connection_angle_limit: AngleLimit, set_angle=Angle(0, numpy.pi/2)):
        self.id = id_
        self.parent = parent
        self.child = child
        self.angle_lim = connection_angle_limit
        self._set_angle(set_angle)
    
    def _set_angle(self, set_angle:Angle):
        if set_angle not in self.angle_lim:
            print(f'{set_angle} not in {self.angle_lim}')
        self.child._update(set_angle, self.parent.end_terminal.glob, self.parent.end_terminal.parent_angle+self.parent.end_terminal.cur_angle)
    
    def _set(self, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None):
        self.child._update(set_angle, offset, parent_angle)

    def _update(self):
        self.child._update(offset=self.parent.end_terminal.glob, parent_angle=self.parent.end_terminal.parent_angle+self.parent.end_terminal.cur_angle)

    def _plot(self, ax: plt.Axes, main=False, annotate=False):
        self.child._plot(ax, annotate)
        if main:
            self.parent._plot(ax, annotate)

def _rad_to_degree(angle):
    return 180*angle/numpy.pi

def _degree_to_rad(angle):
    return angle*numpy.pi/180

def _spherical(r, theta, phi):
    x = r * numpy.cos(theta) * numpy.sin(phi)
    y = r * numpy.sin(theta) * numpy.sin(phi)
    z = r * numpy.cos(phi) 
    return Coordinate(x,y,z)

def _angle(c1: Coordinate, ref: Coordinate=Coordinate(0,0,0)):
    try:
        theta = numpy.arctan((c1.y-ref.y)/(c1.x-ref.x))
    except:
        theta = 0.0
    phi = numpy.arccos((c1.z-ref.z)/(numpy.sqrt((c1.x-ref.x)**2 + (c1.y-ref.y)**2 + (c1.z-ref.z)**2)))

    return Angle(theta, phi)

def _rotatex(x, y, z, delta):
    if numpy.isnan(delta):
        raise ValueError(f'Invalid angle: {delta}')
    nx = x
    ny = y * numpy.cos(delta) - z * numpy.sin(delta)
    nz = y * numpy.sin(delta) + z * numpy.cos(delta)
    return nx, ny, nz

def _rotatey(x, y, z, phi):
    if numpy.isnan(phi):
        raise ValueError(f'Invalid angle: {phi}')
    nx = x * numpy.cos(phi) + z * numpy.sin(phi)
    ny = y
    nz = -x * numpy.sin(phi) + z * numpy.cos(phi)
    return nx, ny, nz

def _rotatez(x, y, z, theta):
    if numpy.isnan(theta):
        raise ValueError(f'Invalid angle: {theta}')
    nx = x * numpy.cos(theta) - y * numpy.sin(theta)
    ny = x * numpy.sin(theta) + y * numpy.cos(theta)
    nz = z
    return nx, ny, nz

def _rotational_angle(angle:Angle):
    c = _spherical(1, angle.theta, angle.phi)
    theta = numpy.arctan(c.y/c.x)
    phi = numpy.arctan(c.z/c.x)
    delta = numpy.arctan(c.z/c.y)
    
    theta = theta if not numpy.isnan(theta) else 0.0
    phi = phi if not numpy.isnan(phi) else 0.0
    delta = delta if not numpy.isnan(delta) else 0.0
    return theta, phi, delta


def rotate(c: Coordinate, angle:Angle):   
    theta, phi, delta = _rotational_angle(angle)
    nx, ny, nz = _rotatey(c.x, c.y, c.z, phi)
    nx, ny, nz = _rotatez(nx, ny, nz, theta)
    nx, ny, nz = _rotatex(nx, ny, nz, delta)
    return Coordinate(nx, ny, nz)

def _radius(c:Coordinate, ref=Coordinate(0,0,0)):
    return numpy.sqrt((c.x-ref.x)**2 + (c.y-ref.y)**2 + (c.z-ref.z)**2)


class Robot:
    def __init__(self, joints: tuple[Joint]):
        self.joints = joints
        self._update_joints()

    def _set_angle(self, joint_id, angle:Angle):
        for joint in self.joints:
            if joint.id == joint_id:
                joint._set_angle(angle)
            else:
                joint._update()

    def _update_joints(self):
        for joint in self.joints:
            joint._update()
    
    def get_joints_positions(self):
        points = []
        for i, joint in enumerate(self.joints):
            points.append(joint.child.end_terminal.glob)
            print(f'Terminal {i}: {joint.child.end_terminal.glob}')
        return points

    def get_joint(self, joint_id) -> Joint:
        for joint in self.joints:
            if joint.id == joint_id:
                return joint
        raise IndexError(f'Robot does not have joint with the id:"{joint_id}"')

# Base
bs = Segment(Dimension(0, 0, 0), Coordinate(0,0,152), main_terminal=Coordinate(0,0,0))
# Segment 1
s1 = Segment(Dimension(149, 149, 217.375), Coordinate(0, 0, 152))
# Segment 2 
s2 = Segment(Dimension(143.392, 116, 541), Coordinate(0, 0, 425), 
             path=(Coordinate(138, 0, 0), Coordinate(138, 0, 425)))
# Segment 3
s3 = Segment(Dimension(114.287, 116, 493), Coordinate(0, 0, 395))
# Segment 4
s4 = Segment(Dimension(88.798, 80, 107.687), Coordinate(102, 0, 120),
             path=(Coordinate(102, 0, 0),))
# Segment 5
s5 = Segment(Dimension(107.687, 80,  88.798), Coordinate(100, 0, 0))

# Joint 1
j1 = Joint(1, bs, s1, AngleLimit(theta=Limit(_degree_to_rad(-175), _degree_to_rad(175)), phi=Limit(_degree_to_rad(180), _degree_to_rad(180))), set_angle=Angle(theta=0))
# Joint 2
j2 = Joint(2, s1, s2, AngleLimit(phi=Limit(_degree_to_rad(-85), _degree_to_rad(265))), set_angle=Angle(phi=0))
# Joint 3
j3 = Joint(3, s2, s3, AngleLimit(phi=Limit(_degree_to_rad(-160), _degree_to_rad(160))), set_angle=Angle(phi=0))
# Joint 4
j4 = Joint(4, s3, s4, AngleLimit(phi=Limit(_degree_to_rad(-265), _degree_to_rad(85))), set_angle=Angle(phi=0))
# Joint 5
j5 = Joint(5, s4, s5, AngleLimit(theta=Limit(_degree_to_rad(-175), _degree_to_rad(175)), phi=Limit(_degree_to_rad(180), _degree_to_rad(180))), set_angle=Angle(theta=0))

class LineGraphApp:
    def __init__(self, root: tk.Tk, robot: Robot):
        self.root = root
        self.root.title("Line Graph")
        self.root.bind('<Destroy>', self._quit)
        
        self.robot = robot

        fig = plt.figure()
        self.ax = fig.add_subplot(projection='3d')
        
        self.canvas = FigureCanvasTkAgg(fig, master=root)
        toolbar = NavigationToolbar2Tk(self.canvas, root)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        

        self.joint_id = tk.Scale(root, resolution=1, label='Joint',   from_=1, to=len(self.robot.joints), command=lambda e=None: self._update_angle_sliders())
        self.joint_id.pack(side='left')

        self.phi = tk.Scale(root, resolution=1e-6, label='Phi',   from_=-numpy.pi/2, to=numpy.pi/2, command=lambda e=None: self.update_plot())
        self.phi.pack(side='left') 
        self.theta = tk.Scale(root, resolution=1e-6, label='Theta', from_=-numpy.pi, to=numpy.pi,   command=lambda e=None: self.update_plot())
        self.theta.pack(side='left')      

        self.plotparent_var = tk.BooleanVar(value=True)
        self.plotparent = tk.Checkbutton(root, text=f'Plot Parents', variable=self.plotparent_var, command=lambda e=None: self.update_plot()).pack()

        self.ax.set_xlim(-1000, 1000)
        self.ax.set_ylim(-1000, 1000)
        self.ax.set_zlim(-1000, 1000)
        self.canvas.draw()

        self._update_angle_sliders()
        self.update_plot()
        
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
    
    def _quit(self, *args):
        self.root.quit()     # stops mainloop

        
    def update_plot(self, *args):
        print()
        set_angle = Angle(self.theta.get(), self.phi.get())
        self.robot._set_angle(int(self.joint_id.get()), set_angle)
        elev = self.ax.elev
        azim = self.ax.azim
        x = self.ax.get_xlim3d()
        y = self.ax.get_ylim3d()
        z = self.ax.get_zlim3d()

        self.ax.clear()
        
        self.ax.text(*self.robot.joints[0].parent.end_terminal.glob, s=f'{self.robot.joints[0].parent.end_terminal.glob}')
        for joint in self.robot.joints:
            joint._plot(self.ax, main=self.plotparent_var.get(), annotate=True)

        self.ax.scatter(-1000, -1000, 0, marker='+') # 'c' sets the color based on 'z' values
        self.ax.scatter(1000, 1000, 1500, marker='+') # 'c' sets the color based on 'z' values
        self.ax.set_xlabel('X axis')
        self.ax.set_ylabel('Y axis')
        self.ax.set_zlabel('Z axis')

        self.ax.set_xlim(x)
        self.ax.set_ylim(y)
        self.ax.set_zlim(z)

        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()
        
        #self.robot.get_joints_positions()

    def _update_angle_sliders(self, *args):
        joint_id = int(self.joint_id.get())
        joint = self.robot.get_joint(joint_id) 
        cur_angle = joint.child.main_terminal.cur_angle

        # Update Limit on sliders
        theta_lim, phi_lim = joint.angle_lim
        self.phi.config(from_=phi_lim.min, to=phi_lim.max)
        self.theta.config(from_=theta_lim.min, to=theta_lim.max)

        # Set slider to current angles for selected joint
        self.phi.set(cur_angle.phi)
        self.theta.set(cur_angle.theta)
        
    

if __name__ == '__main__':
    robot = Robot((j1, j2 , j3, j4, j5))
    root = tk.Tk()
    app = LineGraphApp(root, robot)
    root.mainloop()

    pass