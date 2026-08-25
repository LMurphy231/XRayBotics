from dataclasses import dataclass
from typing import Union
import sympy as sp
import numpy
from  rtypes import *


def _rad_to_degree(angle):
    return 180*angle/numpy.pi

def _degree_to_rad(angle):
    return angle*numpy.pi/180

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
 

if __name__ == "__main__":
    theta = numpy.arange(0, 2*numpy.pi, step=0.01)
    _get_3dim_angles(1.5, 1, 1, 1, 1, theta)
    _get_2dim_angle(1.5, 1, 1, 1)