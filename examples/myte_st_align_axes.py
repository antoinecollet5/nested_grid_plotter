#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 12 10:20:08 2022

@author: acollet
"""

import matplotlib.pyplot as plt
import nested_grid_plotter as ngp
import numpy as np

plotter = ngp.Plotter(
    plt.figure(figsize=(15, 5), constrained_layout=False),
    builder=ngp.SubplotsMosaicBuilder([["ax1-1", "ax1-2", "ax1-3"]]),
)
# Make some data
np.random.seed(1)
data = (np.random.rand(20) + 5) ** 2
data_cum = data.cumsum()

# On the left figure, if we plot the data and its cumulative, the ticks on the y axes
# are not aligned
ax1 = plotter.ax_dict["ax1-1"]
ax1.plot(data)
twin_ax_1 = ax1.twinx()
twin_ax_1.plot(data_cum)
ax1.grid()
twin_ax_1.grid()
ax1.set_title("No alignment")

# This gives the optimal alignment
ax2 = plotter.ax_dict["ax1-2"]
ax2.plot(data)
ax2_twin = ax2.twinx()
ax2_twin.plot(data_cum)
ax2.grid()
ax2_twin.grid()
ngp.align_y_axes([ax2, ax2_twin])
ax2.set_title("Default alignment")

# This is not optimal
ax3 = plotter.ax_dict["ax1-3"]
ax3.plot(data)
ax3_twin = ax3.twinx()
ax3_twin.plot(data_cum)
ax3.grid()
ax3_twin.grid()
ngp.align_y_axes_on_values([ax3, ax3_twin])
ax3.set_title("Specific alignment with no values")

plotter.fig  # to display the figure inline
