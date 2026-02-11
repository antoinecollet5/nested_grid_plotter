# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Antoine COLLET
"""
Purpose
=======

NestedGridPlotter is based on matplotlib and intends to simplify the plotting of
nestedgrid by providing a objected oriented class.

The following functionalities are directly provided on module-level.

Classes
=======

.. autosummary::
   :toctree: _autosummary

    SubfigsBuilder
    SubplotsMosaicBuilder
    Plotter
    NestedGridPlotter
    AnimatedPlotter

Utility Functions
===================

.. autosummary::
   :toctree: _autosummary

    add_grid_and_tick_prams_to_axis
    ticklabels_to_datetime
    add_twin_axis_as_datetime
    add_xaxis_twin_as_date
    align_x_axes
    align_y_axes
    align_x_axes_on_values
    align_y_axes_on_values
    extract_frames_from_embedded_html_animation
    get_line_style
    hide_axis_spine
    hide_axis_ticklabels
    make_patch_spines_invisible
    make_ticks_overlapping_axis_frame_invisible
    make_x_axes_symmetric_zero_centered
    make_y_axes_symmetric_zero_centered
    replace_bad_path_characters
    add_letter_to_frames

Plot functions
==============

.. autosummary::
   :toctree: _autosummary

    multi_imshow

Plot configuration
==================

.. autosummary::
   :toctree: _autosummary

    apply_nice_default_rc_params

"""

from pathlib import Path

from matplotlib.figure import Figure

from nested_grid_plotter.__about__ import __author__, __name__, __version__
from nested_grid_plotter._animated_plotter import AnimatedPlotter
from nested_grid_plotter._base_plotter import (
    NestedGridPlotter,
    Plotter,
    SubfigsBuilder,
    SubplotsMosaicBuilder,
)
from nested_grid_plotter._config import (
    _register_default_fonts,
    apply_nice_default_rc_params,
)
from nested_grid_plotter._imshow import multi_imshow
from nested_grid_plotter._utils import (
    add_grid_and_tick_prams_to_axis,
    add_letter_to_frames,
    add_twin_axis_as_datetime,
    add_xaxis_twin_as_date,
    align_x_axes,
    align_x_axes_on_values,
    align_y_axes,
    align_y_axes_on_values,
    extract_frames_from_embedded_html_animation,
    get_line_style,
    hide_axis_spine,
    hide_axis_ticklabels,
    make_patch_spines_invisible,
    make_ticks_overlapping_axis_frame_invisible,
    make_x_axes_symmetric_zero_centered,
    make_y_axes_symmetric_zero_centered,
    replace_bad_path_characters,
    ticklabels_to_datetime,
)

_register_default_fonts(Path(__file__).parent.joinpath("fonts"))

__all__ = [
    "__version__",
    "__name__",
    "__author__",
    "Figure",
    "SubplotsMosaicBuilder",
    "SubfigsBuilder",
    "Plotter",
    "NestedGridPlotter",
    "AnimatedPlotter",
    "get_line_style",
    "extract_frames_from_embedded_html_animation",
    "make_patch_spines_invisible",
    "replace_bad_path_characters",
    "add_grid_and_tick_prams_to_axis",
    "make_ticks_overlapping_axis_frame_invisible",
    "hide_axis_ticklabels",
    "hide_axis_spine",
    "align_x_axes",
    "align_x_axes_on_values",
    "align_y_axes",
    "align_y_axes_on_values",
    "make_x_axes_symmetric_zero_centered",
    "make_y_axes_symmetric_zero_centered",
    "ticklabels_to_datetime",
    "add_twin_axis_as_datetime",
    "add_xaxis_twin_as_date",
    "multi_imshow",
    "add_letter_to_frames",
    "apply_nice_default_rc_params",
]
