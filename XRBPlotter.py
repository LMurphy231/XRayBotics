import logging
import os
import tkinter as tk

import numpy
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.axes as axes
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

class Plotter:
    def __init__(self, root, **options):
        self.root = root
        self.fig = Figure(figsize=options.get('figsize', (6, 4)), dpi=options.get('dpi', 100))
        self.ax = self.fig.add_subplot(111, projection=options.get('projection', None))

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)

        if options.get('toolbar', True):
            toolbar_frame = tk.Frame(self.root)
            toolbar_frame.grid(row=1, column=0, sticky=tk.W)
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            toolbar.update()

        self.ax.minorticks_on()
        self.ax.grid(True)
        
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky=tk.NSEW)

        # Copycat functions
        self.scatter = self.ax.scatter
        self.plot    = self.ax.plot

    def _update(self):
        self.ax.clear()
        self.canvas.draw()

    



