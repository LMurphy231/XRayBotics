import logging
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


import multiprocessing
import requests
import socket
import threading



import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import numpy

from Robot import RPC

from utill import communications
from utill import consts


class GUI:
    def __init__(self, name = 'XRayBotics'):
        self.window = tk.Tk()
        self.name = name
        self.window.title(name)
        self._create_window()

        self.window.mainloop()

    def _create_window(self):
        self.root = tk.Frame(self.window)
        self.root.grid(row=0, column=0, sticky=tk.NSEW)

        test_setup_frame = tk.Frame(self.root)
        test_setup_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self._create_test_setup(test_setup_frame)
        
    
    def _create_test_setup(self, frame:tk.Frame):
        self.test_name_var = tk.StringVar(value='')
        tk.Label(frame, text='Test Name:').grid(row=0, column=0, sticky=tk.E, padx=5)
        tk.Entry(frame, textvariable=self.test_name_var).grid(row=0, column=1, sticky=tk.EW)

        ttk.Button(frame, text='Select Test', )


if __name__ == '__main__':
    GUI()