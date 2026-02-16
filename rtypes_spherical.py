import dataclasses 
from collections import UserDict
from typing import Union
import tkinter as tk
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D 

import numpy

@dataclasses.dataclass(frozen=True)
class Degree:
    angle: float


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
            return self.radius * other
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

@dataclasses.dataclass(frozen=True)
class Limit:
    min: Union[float, int]
    max: Union[float, int]

    def __contains__(self, other):
        if isinstance(other, (float, int)):
            return other >= self.min and other <= self.max
        raise TypeError(f"unsupported operand type(s) for contains: '{type(self).__name__}' and '{type(other).__name__}'")


@dataclasses.dataclass()
class Angle:
    theta: float
    phi  : float

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
            return _spherical(other.radius, self.theta, self.phi)
        if isinstance(other, Radius):
            return _spherical(other.r, self.theta, self.phi)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

class AngleLimit:
    def __init__(self, theta: Union[Limit, None]=Limit(0, 0), phi:Union[Limit, None]=Limit(0, 0)):
        self.theta = theta
        self.phi   = phi  

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
    
class Position:
    def __init__(self, base: Coordinate, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None): 
        self.base = base
        self.local: Coordinate
        self.glob : Coordinate
        self.cur_angle = set_angle if isinstance(set_angle, Angle) else Angle(0,numpy.pi/2)
        self.parent_angle = parent_angle if isinstance(parent_angle, Angle) else Angle(0,numpy.pi/2)
    
    def __str__(self):
        return f'Base:   {self.base}\nLocal:  {self.local}\nGloabl: {self.glob}'
    
    def _update(self, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None):
        if isinstance(set_angle, Angle):
            self.cur_angle = set_angle
        if isinstance(parent_angle, Angle):
            self.parent_angle = parent_angle
        # Updates local and global positions from on base position
        glob  = Coordinate(self.base.x, self.base.y, self.base.z)

        # Update current angle and get new local coordinate based on that angle
        self.local = self.base * self.cur_angle
         
        # Update Global position
        self.glob = offset + glob * (self.parent_angle + self.cur_angle)

class Segment:
    def __init__(self, dim: Dimension, end_terminal: Coordinate, main_terminal: Coordinate=Coordinate(0.0,0.0,0.0), set_angle: Angle=None, 
                 offset: Coordinate=Coordinate(0.0,0.0,0.0), parent_angle: Angle=None, path: Union[tuple[Coordinate],None]=None):
        self.dim = dim
        self.end_terminal = Position(end_terminal, set_angle, offset, parent_angle)
        self.main_terminal = Position(main_terminal, set_angle, offset, parent_angle)
        self.set_angle = set_angle
        self.offset = offset
        self.path = self._set_path(path)
    
    def _update(self, set_angle:Angle = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Angle = None):
        self.main_terminal._update(set_angle, offset, parent_angle)
        self.end_terminal._update(set_angle, offset, parent_angle)

        for point in self.path:
            point._update(set_angle, offset, parent_angle)

    def _set_path(self, set_path: Union[tuple[Coordinate],None]=None) -> tuple[Position]: 
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

    @property
    def local_angle(self):
        return _angle(self.end_terminal.local, self.main_terminal.local)

    @property
    def global_angle(self):
        return _angle(self.end_terminal.glob, self.main_terminal.glob)



def _rad_to_degree(angle):
    return 180*angle/numpy.pi

def _degree_to_rad(angle):
    return angle*numpy.pi/180

def _spherical(r, theta, phi):
    x = r * numpy.cos(theta) * numpy.sin(phi)
    y = r * numpy.sin(theta) * numpy.sin(phi)
    z = r * numpy.cos(phi) 
    return Coordinate(x,y,z)

def _angle(c1: Coordinate, c2: Coordinate):
    theta = numpy.arctan((c2.y-c1.y)/(c2.x-c1.x))
    phi = numpy.arccos((c2.z-c1.z)/(numpy.sqrt((c2.x-c1.x)**2 + (c2.y-c1.y)**2 + (c2.z-c1.z)**2)))
    return Angle(theta, phi)

def _radius(c1:Coordinate, c2=Coordinate(0,0,0)):
    return numpy.sqrt((c1.x-c2.x)**2 + (c1.y-c2.y)**2 + (c1.z-c2.z)**2)

if __name__ == '__main__':
    pass