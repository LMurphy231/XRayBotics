import dataclasses 
from collections import UserDict
from typing import Union
import tkinter as tk
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D 

import numpy



class Position:
    pass

class Section:
    pass

@dataclasses.dataclass()
class Coordinate:
    x: float
    y: float
    z: float
    def __str__(self):
        return f'x: {self.x:>5.4g}, y: {self.y:>5.4g}, z: {self.z:>5.4g}'
    
    def get(self):
        return self.x, self.y, self.z
    
    def __add__(self, other):
        if isinstance(other, Coordinate):
            return Coordinate(self.x+other.x, self.y+other.y, self.z+other.z)
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iadd__(self, other):
        if isinstance(other, Coordinate):
            self.x += other.x 
            self.y += other.y 
            self.z += other.z
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        if isinstance(other, Coordinate):
            return Coordinate(self.x-other.x, self.y-other.y, self.z-other.z)
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __isub__(self, other):
        if isinstance(other, Coordinate):
            self.x -= other.x 
            self.y -= other.y 
            self.z -= other.z
            return
        raise TypeError(f"unsupported operand type(s) for -=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __mul__(self, other):
        if isinstance(other, (Coordinate)):
            return self.x*other.x + self.y*other.y+ self.z*other.z
        if isinstance(other, (float, int)):
            return Coordinate(self.x*other, self.y*other, self.z*other)
        if isinstance(other, Rotation):
            nx, ny, nz = _rotatex(self.x, self.y, self.z, other.delta)
            nx, ny, nz = _rotatey(nx, ny, nz, other.phi)
            nx, ny, nz = _rotatez(nx, ny, nz, other.theta)
            return Coordinate(nx, ny, nz)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

    def __imul__(self, other):
        if isinstance(other, Rotation):
            nx, ny, nz = _rotatex(self.x, self.y, self.z, other.delta)
            nx, ny, nz = _rotatey(nx, ny, nz, other.phi)
            self.x, self.y, self.z = _rotatez(nx, ny, nz, other.theta)
            return self
        if isinstance(other, (float, int)):
            self.x *= other
            self.y *= other
            self.z *= other
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    @property
    def radius(self):
        return _get_radius(self)

class Line:
    def __init__(self, pos1: Coordinate, pos2: Coordinate):
        self.pos1 = pos1
        self.pos2 = pos2
        self.radius = self._radius()

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
        if isinstance(other, (float, int, Rotation)):
            return Line(self.pos1 * other, self.pos2 * other)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

    def __imul__(self, other):
        if isinstance(other, Rotation):
            self.pos1 *= other
            self.pos2 *= other
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iter__(self):
        return (axis for axis in [*zip(self.pos1, self.pos2)])
    
    def _radius(self):
        return _get_radius(self.pos1, self.pos2)

@dataclasses.dataclass()
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

    @property
    def locked(self):
        return True if self.min == self.max else False

@dataclasses.dataclass()
class Locked:
    theta: bool
    phi  : bool
    delta: bool
    
    def __iter__(self):
        yield self.theta
        yield self.phi  
        yield self.delta

class Radius:
    def __init__(self, r: Union[float, int]):
        self.r = r

    def __mul__(self, other):
        if isinstance(other, Rotation):
            x = self.r*numpy.cos(other.theta) * numpy.sin(other.phi)
            y = self.r*numpy.sin(other.theta) * numpy.sin(other.phi)
            z = self.r*numpy.cos(other.phi)
            return Coordinate(x,y,z)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

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
        if isinstance(other, Angle):
            return Angle(self.theta*other.theta, self.phi*other.phi)
        if isinstance(other, Coordinate):
            return rotate(other, self)
        if isinstance(other, Radius):
            return _spherical(other.r, self.theta, self.phi)
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")
    
@dataclasses.dataclass()
class Rotation:
    theta: float
    phi  : float
    delta: float
    
    def __str__ (self):
        return f'Theta: {self.theta}, Phi: {self.phi}, Delta: {self.delta}'
    
    def __add__(self, other):
        if isinstance(other, Rotation):
            return Rotation(self.theta+other.theta, self.phi+other.phi, self.delta+other.delta)
        raise TypeError(f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __iadd__(self, other):
        if isinstance(other, Rotation):
            self.theta += other.theta 
            self.phi   += other.phi 
            self.delta += other.delta
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __sub__(self, other):
        if isinstance(other, Rotation):
            return Rotation(self.theta-other.theta, self.phi-other.phi, self.delta-other.delta)
        raise TypeError(f"unsupported operand type(s) for -: '{type(self).__name__}' and '{type(other).__name__}'")
    
    def __isub__(self, other):
        if isinstance(other, Rotation):
            self.theta -= other.theta 
            self.phi   -= other.phi 
            self.delta -= other.delta
            return self
        raise TypeError(f"unsupported operand type(s) for -=: '{type(self).__name__}' and '{type(other).__name__}'")

    def __mul__(self, other):
        if isinstance(other, Rotation):
            return Rotation(self.theta*other.theta, self.phi*other.phi, self.delta*other.delta)
        if isinstance(other, (float, int)):
            return Coordinate(other,0,0)*self
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

    def __rmul__(self, other):
        if isinstance(other, (float, int)):
            return Coordinate(other,0,0)*self
        raise TypeError(f"unsupported operand type(s) for *: '{type(self).__name__}' and '{type(other).__name__}'")

    def __imul__(self, other):
        if isinstance(other, Rotation):
            self.theta *= other.theta 
            self.phi   *= other.phi 
            self.delta *= other.delta
            return self
        raise TypeError(f"unsupported operand type(s) for +=: '{type(self).__name__}' and '{type(other).__name__}'")

    def __neg__(self):
        return Rotation(-self.theta, -self.phi, -self.delta)

        
class RotationalLimit:
    def __init__(self, theta: Union[Limit, None]=None, phi:Union[Limit, None]=None, delta:Union[Limit, None]=None):
        self.theta = theta if theta is not None else Limit(0, 0)
        self.phi   = phi   if phi   is not None else Limit(0, 0)
        self.delta = delta if delta is not None else Limit(0, 0)

    def __contains__(self, item):
        if isinstance(item, Rotation):
            if item.theta not in self.theta:
                return False
            if item.phi not in self.phi:
                return False
            if item.delta not in self.delta:
                return False
            return True
        raise TypeError(f"Item type '{type(item).__name__}' must be a Rotation")
    
    def __str__(self):
        return f'Theta: {self.theta} Phi: {self.phi} Delta: {self.delta}  '
    
    def __iter__(self):
        yield self.theta
        yield self.phi
        yield self.delta

    @property
    def lock(self):
        return Rotation(0.0 if self.theta.locked else 1.0, 0.0 if self.phi.locked else 1.0, 0.0 if self.delta.locked else 1.0)

@dataclasses.dataclass()
class Position:
    def __init__(self, base: Coordinate, set_angle:Rotation = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Rotation = None): 
        self.base = base
        self.local: Coordinate
        self.glob : Coordinate
        self.cur_angle = set_angle

        self.cur_angle = set_angle if isinstance(set_angle, Rotation) else Rotation(0,0,0)
        self.parent_angle = parent_angle if isinstance(parent_angle, Rotation) else Rotation(0,0,0)

        self._update(set_angle, offset=offset, parent_angle=parent_angle)
    
    def __str__(self):
        return f'Base:   {self.base}\nLocal:  {self.local}\nGloabl: {self.glob}'
    
    def _update(self, set_angle:Rotation = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Rotation = None):
        if isinstance(parent_angle, Rotation):
            self.parent_angle = parent_angle
        if isinstance(set_angle, Rotation):
            self.cur_angle = set_angle

        # Updates local and global positions from on base position
        glob  = Coordinate(self.base.x, self.base.y, self.base.z)

        # Update current angle and get new local coordinate based on that angle
        self.local = self.base * self.cur_angle
         
        # Update Global position
        self.glob = offset + glob * (self.parent_angle + self.cur_angle)

    
class Segment:
    def __init__(self, dim: Dimension, end_terminal_coord: Coordinate, radius: Union[float, int], set_angle:Rotation = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Rotation = None):
        self.dim = dim
        # TODO make bbox for joint

        self.main_terminal = Position(Coordinate(0,0,0), set_angle, offset, parent_angle)
        self.end_terminal = Position(end_terminal_coord, set_angle, offset, parent_angle)
        self.path = self._create_path()
        self.radius = radius
        self.affected_radius = 0.0

    def _update(self, set_angle:Rotation = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Rotation = None):
        self.main_terminal._update(set_angle, offset, parent_angle)
        self.end_terminal._update(set_angle, offset, parent_angle)

        for point in self.path:
            point._update(set_angle, offset, parent_angle)

    def _get_lines(self) -> tuple[Line]:
        lines = []
        prev_pos = self.main_terminal
        for pos in self.path:
            lines.append(Line(prev_pos.glob, pos.glob))
            prev_pos = pos
        lines.append(Line(prev_pos.glob, self.end_terminal.glob))
        return tuple(lines)

    def _get_length(self):
        return self.end_terminal.glob - self.main_terminal.glob
    
    def _create_path(self) -> tuple[Position]:
        x1, y1, z1 = self.main_terminal.base
        x2, y2, z2 = self.end_terminal.base
        path = []
        if z1 != z2:
            path.append(Position(Coordinate(x1, y1, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
        if y1 != y2:
            path.append(Position(Coordinate(x1, y2, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
        if x1 != x2:
            path.append(Position(Coordinate(x2, y2, z2), self.main_terminal.cur_angle, self.main_terminal.glob, self.main_terminal.parent_angle))
        
        
        return tuple(path)
        
    def _plot(self, ax: plt.Axes, annotate=False, color='red'):
        ax.scatter(*(self.end_terminal.glob), marker='+', c=color)
        ax.scatter(*(self.main_terminal.glob), marker='o')
        if annotate:
            ax.text(*self.end_terminal.glob, s=f'{self.end_terminal.glob}')
        lines = self._get_lines()
        for line in lines:
            ax.plot(*line)
            
    # TODO: Create a _place function that allows segment to be placed a specific coordinate using either main or end terminal

class Joint:
    def __init__(self, id_, parent: Segment, child: Segment, connection_rotation_limit: RotationalLimit):
        self.id = id_
        self.parent = parent
        self.child = child
        self.rotation_lim = connection_rotation_limit
        self.parent.affected_radius = self._affected_radius(self.parent)
        self.child.affected_radius = self._affected_radius(self.child)
        self.radius = _get_radius(self.parent.end_terminal.base, self.child.end_terminal.base)

    def _set_angle(self, set_angle:Rotation):
        if set_angle * self.rotation_lim.lock not in self.rotation_lim:
            print(f'{set_angle} not in {self.rotation_lim}')
        self.child._update(set_angle * self.rotation_lim.lock, self.parent.end_terminal.glob, self.parent.end_terminal.parent_angle+self.parent.end_terminal.cur_angle)
    
    def _set(self, set_angle:Rotation = None, offset:Coordinate = Coordinate(0,0,0), parent_angle:Rotation = None):
        self.child._update(set_angle * self.rotation_lim.lock, offset, parent_angle)
        
    def _update(self):
        self.child._update(offset=self.parent.end_terminal.glob, parent_angle=self.parent.end_terminal.parent_angle+self.parent.end_terminal.cur_angle)

    def _angle_is_allowed(self, set_angle: Rotation):
        return set_angle in self.rotation_lim

    def _plot(self, ax: plt.Axes, main=False, annotate=False):
        self.child._plot(ax, annotate)
        if main:
            self.parent._plot(ax, annotate)

    def _affected_radius(self, seg: Segment):
        return seg.end_terminal.base.z
        #if not self.rotation_lim.locked.theta:
        #    return seg.end_terminal.base.z
        #if not self.rotation_lim.locked.phi:
        #    return seg.end_terminal.base.y
        #if not self.rotation_lim.locked.delta:
        #    return seg.end_terminal.base.x

    # TODO: Create a _place function that allows joint to be placed a specific coordinate



def _get_angle(c1: Coordinate, c2: Coordinate):
    theta = numpy.arctan((c2.y-c1.y)/(c2.x-c1.x))
    phi = numpy.arccos((c2.z-c1.z)/(numpy.sqrt((c2.x-c1.x)**2 + (c2.y-c1.y)**2 + (c2.z-c1.z)**2)))
    return Rotation(theta, phi, 0.0)

def _spherical(r, theta, phi):
    x = r * numpy.cos(theta) * numpy.sin(phi)
    y = r * numpy.sin(theta) * numpy.sin(phi)
    z = r * numpy.cos(phi) 
    return Coordinate(x,y,z)

    
class Effector:
    def __init__(self, x_wrist: Joint, z_wrist: Joint):
        self.z_wrist = z_wrist
        self.x_wrist = x_wrist
        # For now, use the x_write end terminal as the point of reference
        self.effector_pos = self.x_wrist.child.end_terminal

    def _set(self, cord: Coordinate, angle: Rotation):
        return
        

    def __contains__(self, item):
        if isinstance(item, (Joint)):
            return item is self.z_wrist or item is self.x_wrist
        raise TypeError(f"Item type '{type(item).__name__}' must be a Joint")


class Bbox(UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO Change from dict class and make it solely for bbox 
        
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
    
    def __contains__(self, data):
        #TODO Check to see if data is within Bbox, compare with global coordinates
        raise NotImplementedError
    
    def _lines(self):
        # TODO create lines here instead of 
        raise NotImplementedError

    
class Segment1:
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
        self.bbox = Bbox()
        coord =  self.main_terminal_point
        for z in range(2):
            for y in range(2):
                for x in range(2):
                    cx = (x*self.l - coord.x)
                    cy = (y*self.w - coord.y)
                    cz = (z*self.h - coord.z)
                    self.bbox[x, y, z] = Coordinate(cx, cy, cz)
    
    def __str__(self):
        item_name = f'Main Terminal:\n{self.main_terminal_point}\n\nWith corners:\n'
        for key, coordinate in self.bbox:
            item_name += f'{key} = {coordinate}\n'
        return item_name

    def _get_shape(self):
        # TODO move to Bbox
        def _flip_bit(key):
            return 1 if key == 0 else 0
        
        lines = []
        points = []
        data = {}
        for keys, coordinate in self.bbox:
            points.append(coordinate)
            data[keys] = coordinate
        used_keys = []
        for keys in data:
            for i, key in enumerate(keys):
                key_pair = list(keys[:])
                key_pair[i] = _flip_bit(key)
                if key_pair in used_keys:
                    continue
                lines.append(Line(data[keys], data[tuple(key_pair)]))
            used_keys.append(list(keys))

        return points, lines


@dataclasses.dataclass()
class Terminal:
    position : Coordinate
    normal   : Rotation
    cur_dir  : Rotation
    parent   : Segment
    child    : Segment


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

def _rotatexyz(x, y, z, theta, phi, delta):   
    nx, ny, nz = _rotatey(x, y, z, phi)
    nx, ny, nz = _rotatez(nx, ny, nz, theta)
    nx, ny, nz = _rotatex(nx, ny, nz, delta)
    return nx, ny, nz

def _get_radius(c1:Coordinate, c2=Coordinate(0,0,0)):
    return numpy.sqrt((c1.x-c2.x)**2 + (c1.y-c2.y)**2 + (c1.z-c2.z)**2)

def _rad_to_degree(angle):
    return 180*angle/numpy.pi

def _degree_to_rad(angle):
    return angle*numpy.pi/180


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

def _get_2dim_angle(r1, r2, x1, y1):
    a = numpy.arccos((r1**2 - x1**2 - y1**2 - r2**2)/(2*r2*numpy.sqrt(x1**2 + y1**2)))
    b = numpy.arctan(y1/x1)
    theta =  (-a+b, a+b)
    return theta

def _get_3dim_angles(r1, r2, x1, y1, z1, theta):
    a = z1
    b = lambda theta: numpy.sqrt(x1**2+y1**2) * numpy.cos(theta - numpy.atan(y1/x1))
    c = (r1**2 - x1**2 - y1**2 - z1**2 - r2**2)/(2*r2)    
    
    phi = lambda theta: numpy.acos(c/numpy.sqrt(a**2 + b(theta)**2))+ numpy.acos(b(theta)/a)

    test = lambda theta: numpy.sqrt(a**2 + b(theta)**2) * numpy.cos(phi(theta) - numpy.atan(b(theta)/a))
    results = []
    list = numpy.column_stack((theta, phi(theta), test(theta)))
    for i, (th, ph, ts) in enumerate(list):
        if i == 0:
            continue
        #print(i, list[i-1,2])
        if (ts >= 0 and list[i-1,2] <= 0) or (ts <= 0 and list[i-1,2] >= 0): 
            x = r2*numpy.cos(th)*numpy.sin(ph) + x1
            y = r2*numpy.sin(th)*numpy.sin(ph) + y1
            z = r2*numpy.cos(ph) + z1
            r = numpy.sqrt(x**2 + y**2 + z**2)
            R = numpy.sqrt((x - x1)**2 + (y - y1)**2 + (z - z1)**2)
            print(f'{th:<4.3f}: {ph:<4.3f}, ts: {ts:>4.3f}, x: {x:>3.3f}, y: {y:>3.3f}, z: {z:>3.3f}, r: {r:>3.3f} R: {R:>3.3f}')
            results.append(th, ph)
    return results

def _translate_angle_to_direction(r: float, angle: Rotation):
    x = numpy.sqrt(r**2/(1 + numpy.tan(angle.theta)**2 + numpy.tan(angle.phi)**2))
    y = x * numpy.tan(angle.theta)
    z = x * numpy.tan(angle.phi)
    return Coordinate(x,y,z)

def _get_rotational_angles(c1: Coordinate, c2: Coordinate = Coordinate(0,0,0)):
    theta = numpy.arctan((c1.y - c2.y)/(c1.x - c2.x))
    phi = numpy.arctan((c1.z - c2.z)/(c1.x - c2.x))
    delta = numpy.arctan((c1.z - c2.z)/(c1.y - c2.y))
    return Rotation(theta, phi, delta)

# Base
bs = Segment(Dimension(0, 0, 0), Coordinate(0,0,0), 138)
# Segment 1
s1 = Segment(Dimension(149, 149, 217.375), Coordinate(138, 0, 152), 152)
# Segment 2 
s2 = Segment(Dimension(143.392, 116, 541), Coordinate(-138, 0, 425), 425)
# Segment 3
s3 = Segment(Dimension(114.287, 116, 493), Coordinate(102, 0, 395), 395)
# Segment 4
s4 = Segment(Dimension(88.798, 80, 107.687), Coordinate(0, 0, 102), 102)
# Segment 5
s5 = Segment(Dimension(107.687, 80,  88.798), Coordinate(100, 0, 0), 100)

# Joint 1
j1 = Joint(1, bs, s1, RotationalLimit(Limit(_degree_to_rad(-175), _degree_to_rad(175)), None, None))
# Joint 2
j2 = Joint(2, s1, s2, RotationalLimit(None, None, Limit(_degree_to_rad(-85), _degree_to_rad(265))))
# Joint 3
j3 = Joint(3, s2, s3, RotationalLimit(None, None, Limit(_degree_to_rad(-160), _degree_to_rad(160))))
# Joint 4
j4 = Joint(4, s3, s4, RotationalLimit(None, None, Limit(_degree_to_rad(-265), _degree_to_rad(85))))
# Joint 5
j5 = Joint(5, s4, s5, RotationalLimit(Limit(_degree_to_rad(-175), _degree_to_rad(175)), None, None))



class Robot:
    def __init__(self, joints: tuple[Joint]):
        self.joints = joints
        self.effector = Effector(self.joints[3],self.joints[4])
        self._update_joints()
        self.eff = Effector(j4,j5)
        

    def _update_joints(self):
        for joint in self.joints:
            joint._update()
            
    def _set_angle(self, joint_id, angle:Rotation):
        for joint in self.joints:
            if joint.id == joint_id:
                joint._set_angle(angle)
            else:
                joint._update()
            
    def get_joints_positions(self):
        points = []
        for i, joint in enumerate(joints):
            points.append(joint.child.end_terminal.glob)
            print(f'Terminal {i}: {joint.child.end_terminal.glob}')
        return points
    
    def get_joint(self, joint_id) -> Joint:
        for joint in joints:
            if joint.id == joint_id:
                return joint
        return None

    def get_length(self):
        length = self.joints[0].parent._get_length()
        for joint in self.joints:
            length += joint.child._get_length()
        return length


    def _get_affected_radius(self, joint_id):
        start_recording = False
        total_length = 0.0
        for joint in reversed(self.joints):
            if start_recording:
                total_length += joint.child.affected_radius
            if joint.id == joint_id:
                start_recording = True
                #total_length -= joint.parent.affected_radius
        return total_length
    
    def _go_to_coords(self, cord: Coordinate):
        angle = _get_rotational_angles(cord)
        r = _get_radius(cord)
        print(f'r: {r}, Theta: {angle.theta}, phi: {angle.phi}, Delta: {angle.delta}')
        for joint in reversed(self.joints):
            t, p, d = joint.rotation_lim.locked
            r1 = self._get_affected_radius(joint.id)
            r2 = joint.parent.affected_radius
            if r1+r2 < r:
                raise ValueError(f'Coordinate outside range')
            
            if not t:
                print(f'{joint.id}: Theta Unlocked {joint.rotation_lim.theta}')
            if not p:
                print(f'{joint.id}: Phi Unlocked {joint.rotation_lim.phi  }')
            if not d:
                print(f'{joint.id}: Delta Unlocked {joint.rotation_lim.delta}')

        #for joint in reversed(self.joints):
        #    theta = numpy.arange(0, 2*numpy.pi, step=0.01)
        #    r1 = self._get_affected_radius(joint.id)
        #    r2 = joint.parent.affected_radius
        #    
        #    if r2 == 0 or joint.id != self.joints[-2].id:
        #        continue
        #    print(f'{joint.id}: r1: {self._get_affected_radius(joint.id)}, r2: {joint.child.affected_radius}')
        #    
        #    print(_get_3dim_angles(self._get_affected_radius(joint.id), joint.child.affected_radius, x, y, z, theta))
            
           







def plot_terminal(ax, terminal: Terminal, offset: Coordinate = Coordinate(1, 0.0, 0.0)):
    pos = terminal.position
    norm = terminal.normal

    parent = terminal.parent
    child = terminal.child

    plot_bbox(ax, parent, terminal_color='red')
    plot_bbox(ax, child, direction=norm)

def plot_bbox(ax: plt.Axes, bbox: Segment, direction: Rotation=Rotation(0.0,numpy.pi/2,0.0), offset: Coordinate = Coordinate(0.0, 0.0, 0.0), 
              show_bbox=True, pointcolor='purple', linecolor= 'green', terminal_color='orange'):
    
    points, lines = bbox.shape
    terminal_coord = bbox.main_terminal_point

    # Plot Bbox Points
    for point in points: 
        ax.scatter(*(offset+point*direction), c=pointcolor) 
    print(points[0])
    # Plot Main Termina
    ax.scatter(*(offset+(points[0]+bbox.main_terminal_point)*direction), c=terminal_color, marker='+') 
    
    # Plot Bbox Lines
    for terminal in bbox.sub_terminal_points:
        ax.scatter(*(offset+(points[0]+terminal)*direction), c=terminal_color, marker='+') 

    # Set labels
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    for line in lines:
        # Create the plot
        ax.plot(*((line+offset)*direction), color=linecolor)

    # Set labels
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')
    







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

        self.phi = tk.Scale(root, resolution=0.0001, label='Phi',   from_=-numpy.pi/2, to=numpy.pi/2, command=lambda e=None: self.update_plot())
        self.phi.pack(side='left') 
        self.theta = tk.Scale(root, resolution=0.0001, label='Theta', from_=-numpy.pi, to=numpy.pi,   command=lambda e=None: self.update_plot())
        self.theta.pack(side='left')
        self.delta = tk.Scale(root, resolution=0.0001, label='Delta', from_=0,         to=2*numpy.pi, command=lambda e=None: self.update_plot())
        self.delta.pack(side='left')

        

        self._update_angle_sliders()
        self.update_plot()
        
        
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.ax.set_autoscale_on(False)
    
    def _quit(self, *args):
        self.root.quit()     # stops mainloop

        
    def update_plot(self, *args):
        set_angle = Rotation(self.theta.get(), self.phi.get(), self.delta.get())
        self.robot._set_angle(int(self.joint_id.get()), set_angle)

        self.ax.clear()
        self.ax.text(*self.robot.joints[0].parent.end_terminal.glob, s=f'{self.robot.joints[0].parent.end_terminal.glob}')
        #self.robot.eff._set(cord=Coordinate(202,0, 1074), angle=Rotation(numpy.pi, numpy.pi, 0))
        for joint in self.robot.joints:
            joint._plot(self.ax, main=True, annotate=True)

        self.ax.scatter(-1000, -1000, 0, marker='+') # 'c' sets the color based on 'z' values
        self.ax.scatter(1000, 1000, 1500, marker='+') # 'c' sets the color based on 'z' values
        #self.robot._go_to_coords(Coordinate(202, 0, 1074))
        self.canvas.draw_idle()

    def _update_angle_sliders(self, *args):
        joint_id = int(self.joint_id.get())
        joint = self.robot.get_joint(joint_id) 
        cur_angle = joint.child.main_terminal.cur_angle

        # Update Limit on sliders
        theta_lim, phi_lim, delta_lim = joint.rotation_lim
        self.phi.config(from_=phi_lim.min, to=phi_lim.max)
        self.theta.config(from_=theta_lim.min, to=theta_lim.max)
        self.delta.config(from_=delta_lim.min, to=delta_lim.max)

        # Set slider to current angles for selected joint
        self.phi.set(cur_angle.phi)
        self.theta.set(cur_angle.theta)
        self.delta.set(cur_angle.delta)
        
        



if __name__ == "__main__":

    joints = (j1, j2, j3, j4, j5)
    robot = Robot(joints)
    


    root = tk.Tk()
    app = LineGraphApp(root, robot)
    root.mainloop()

