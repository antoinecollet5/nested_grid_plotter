"""
Utilities for matplotlib.
"""

import base64
import re
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from dateutil.relativedelta import relativedelta
from matplotlib.axes import Axes
from typing_extensions import Literal

# pylint: disable=C0103 # does not confrom to snake case naming style
# pylint: disable=R0913 # too many arguments
# pylint: disable=R0914 # too many local variables


def get_line_style(line_style_label: str) -> Tuple[float, Tuple[float]]:
    """
    Get a parametrized linestyle from a line style label.

    See https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html

    If a non correct value is given, the solid item is returned by default.

    Parameters
    ----------
    line_style_label : str
        Desired line style label.

    Returns
    -------
    tuple(int)
        The line style parameters.

    """
    return {
        "solid": (0, ()),
        "loosely dotted": (0, (1, 10)),
        "dotted": (0, (1, 5)),
        "densely dotted": (0, (1, 1)),
        "loosely dashed": (0, (5, 10)),
        "dashed": (0, (5, 5)),
        "densely dashed": (0, (5, 1)),
        "loosely dashdotted": (0, (3, 10, 1, 10)),
        "dashdotted": (0, (3, 5, 1, 5)),
        "densely dashdotted": (0, (3, 1, 1, 1)),
        "loosely dashdotdotted": (0, (3, 10, 1, 10, 1, 10)),
        "dashdotdotted": (0, (3, 5, 1, 5, 1, 5)),
        "densely dashdotdotted": (0, (3, 1, 1, 1, 1, 1)),
    }.get(line_style_label, (0, ()))


def make_patch_spines_invisible(ax: Axes) -> None:
    """
    Make patch and spines of the ax invisible.

    Useful for creating a 2nd twin-x axis on the right/left.

    Parameters
    ----------
    ax : Axes
        Axis to modify.

    Examples
    --------
        fig, ax=plt.subplots()
        ax.plot(x, y)
        tax1=ax.twinx()
        tax1.plot(x, y1)
        tax2=ax.twinx()
        tax2.spines['right'].set_position(('axes',1.09))
        make_patch_spines_invisible(tax2)
        tax2.spines['right'].set_visible(True)
        tax2.plot(x, y2)

    Returns
    -------
    None
    """
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def extract_frames_from_embedded_html_animation(
    fpath: Union[str, Path],
    target_path: Optional[Union[str, Path]] = None,
) -> None:
    """
    Extract the embedded frames from an html animation created with matplotlib.

    Parameters
    ----------
    fpath : Union[str, Path]
        Path to the html file.
    target_path : Optional[Union[str, Path]]
        Target path where to store the extracted frames. If None, a folder with
        the name of the html file is created at the location of the html file. If
        default is None.

    Notes
    -----
    The frame format is retrieved automatically.

    """
    input_text: str = Path(fpath).read_text()  # make sure we have a Path instance
    if target_path is None:
        _target_path: Path = Path(fpath).parent.joinpath(Path(fpath).stem)
    else:
        _target_path: Path = Path(target_path)
    _target_path.mkdir(parents=True, exist_ok=True)  # make sure the output path exists

    pattern = re.compile(
        r"frames\[(?P<frame_index>[\d]+)\]\s=\s\"data:image/"
        r'(?P<frame_format>jpeg|tiff|png|svg\+xml);base64,(?P<content>[^ "]+)"'
    )

    # Iterate the patterns
    for m in pattern.finditer(input_text):
        res = m.groupdict()
        frame_format = res.get("frame_format")
        if frame_format == r"svg+xml":
            frame_format = "svg"
        path = _target_path.joinpath(
            f"frame{int(res.get('frame_index')):0>7d}.{frame_format}"
        )
        if frame_format == "svg":
            path.write_text(
                base64.b64decode(res.get("content").encode("utf-8")).decode("utf-8")
            )
        else:
            base64_img_bytes = res.get("content").encode("utf-8")
            path.write_bytes(base64.decodebytes(base64_img_bytes))


def replace_bad_path_characters(filename: str, repchar: str = "_") -> str:
    """
    Make filename compatible with path by replacement.

    Replace anything that isn't alphanumeric, -, _, a space, or a period.
    Note that leading and trailing white spaces and replacement characters
    are also removed.

    Parameters
    ----------
    filename : str
        Old filename.
    repchar : str, optional
        The string to replace the bad values with. The default is "_".

    Returns
    -------
    str
        New filename.

    """
    return re.sub(r"[^\w\-_\. \[\]\(\)]+", repchar, filename).strip(f" {repchar}")


def add_grid_and_tick_prams_to_axis(
    ax: Axes,
    which: Literal["minor", "major", "both"] = "both",
    direction: Literal["in", "out", "inout"] = "in",
    length: float = 10,
    width: float = 1.5,
    colors: Any = "k",
    grid_alpha: float = 1,
    grid_color: Any = "grey",
    grid_linewidth: float = 1.0,
    grid_linestyle: Any = get_line_style("dotted"),
    bottom: bool = True,
    top: bool = True,
    left: bool = True,
    right: bool = True,
    **kwargs: Any,
) -> None:
    """
    Add a grid and configure the thick for a given axis.

    By default, add a grey grid with inner black ticks on the four edges.

    Parameters
    ----------
    ax: Axes
        Ax to modify.
    which : Literal["minor", "major", "both"], optional
        The group of ticks to which the parameters are applied.
        The default is "both".
    direction : Literal['in', 'out', 'inout'], optional
        Puts ticks inside the axes, outside the axes, or both.
        The default is "in".
    length : float, optional
        Tick length in points. The default is 10.
    width : float, optional
        Tick width in points. The default is 1.5.
    colors : Any, optional
        Tick color and label colors. The default is "k".
    grid_alpha : float, optional
        Transparency of gridlines: 0 (transparent) to 1 (opaque).
        The default is 0.5.
    grid_color : Any, optional
        Gridline color. The default is 'lightgrey'.
    grid_linewidth : float, optional
        Width of gridlines in points. The default is 1.
    grid_linestyle : str, optional
        Any valid Line2D line style spec.
        The default is `get_line_style('dotted')`.
    bottom : bool, optional
        Whether to draw the bottom ticks. The default is True.
    top : bool, optional
        Whether to draw the top ticks. The default is True.
    left : bool, optional
        Whether to draw the left ticks. The default is True.
    right : bool, optional
        Whether to draw the right ticks. The default is True.
    **kwargs : Any
        Other parameters for `matplotlib.axes.Axes.tick_params`.

    Returns
    -------
    None
    """
    ax.grid(True)  # Add the grid
    ax.tick_params(
        which=which,
        direction=direction,
        length=length,
        width=width,
        colors=colors,
        grid_alpha=grid_alpha,
        grid_color=grid_color,
        grid_linewidth=grid_linewidth,
        grid_linestyle=grid_linestyle,
        top=top,
        right=right,
        bottom=bottom,
        left=left,
        **kwargs,
    )


def make_ticks_overlapping_axis_frame_invisible(ax: Axes) -> None:
    """
    Make the ticks overlapping the frame of the axis invisible.

    It does not modify the labels, only make the ticks overlapping
    the frame edges as transparent.

    Parameters
    ----------
    ax_name : str
        The given axis name.

    Returns
    -------
    None.

    """
    # For the x axis
    xticks = ax.get_xticks()
    xlines = ax.xaxis.get_ticklines()
    xlim = ax.get_xlim()
    if xticks[0] == xlim[0]:
        xlines[0].set_visible(False)  # Most left tick of the bottom edge
        xlines[1].set_visible(False)  # Most right tick of the bottom edge
    if xticks[-1] == xlim[-1]:
        xlines[-2].set_visible(False)  # Most left tick of the top edge
        xlines[-1].set_visible(False)  # Most right tick of the top edge

    # For the y axis
    yticks = ax.get_yticks()
    ylines = ax.yaxis.get_ticklines()
    ylim = ax.get_ylim()
    if yticks[0] == ylim[0]:
        ylines[0].set_visible(False)  # Bottom tick of the left edge
        ylines[1].set_visible(False)  # Bottom tick of the right edge
    if yticks[-1] == ylim[-1]:
        ylines[-2].set_visible(False)  # Top tick of the left edge
        ylines[-1].set_visible(False)  # Top tick of the right edge


def hide_axis_ticklabels(ax: Axes, which: Literal["both", "x", "y"] = "both") -> None:
    """
    Hide x, y or both x and y ticklabels of the given axis.

    Parameters
    ----------
    ax_name : str
        Name of the axis.
    which : Literal["both", "x", "y"], optional
        The axis to apply the changes on. The default is "both".

    Returns
    -------
    None

    """
    if which in ["both", "x"]:
        plt.setp(ax.get_xticklabels(), visible=False)
        plt.setp(ax.get_xticklines(), visible=False)
    if which in ["both", "y"]:
        plt.setp(ax.get_yticklabels(), visible=False)
        plt.setp(ax.get_yticklines(), visible=False)


def hide_axis_spine(
    ax: Axes, loc: Literal["top", "bottom", "left", "right", "all"]
) -> None:
    """
    Hide one or all spines of the given axis.

    Parameters
    ----------
    ax : Axes
        Axis for which to hide the spines.
    loc : Literal["top", "bottom", "left", "right", "all"]
        The spine to apply the changes on.

    Returns
    -------
    None

    """
    if loc == "all":
        for _loc in ["right", "left", "bottom", "top"]:
            ax.spines[_loc].set_visible(False)
    else:
        ax.spines[loc].set_visible(False)


def align_x_axes(axes: List[Axes], is_ticks_major: bool = True) -> List[Any]:
    """
    Align the ticks of multiple x axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose yaxis ticks are to be aligned.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    return _align_axes(axes, is_ticks_major, False)


def align_y_axes(axes: List[Axes], is_ticks_major: bool = True) -> List[Any]:
    """
    Align the ticks of multiple y axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose yaxis ticks are to be aligned.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    return _align_axes(axes, is_ticks_major, True)


def _align_axes(
    axes: List[Axes], is_ticks_major: bool = True, is_y_axis: bool = True
) -> List[Any]:
    """
    Align the ticks of multiple y axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose yaxis ticks are to be aligned.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.
    is_y_axis:
        Whether to perform the alignment on the y-axis. If False, perform it on the
        x axis. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    n_ax = len(axes)
    if is_y_axis:
        ticks = [aii.get_yticks(minor=not is_ticks_major) for aii in axes]
    else:
        ticks = [aii.get_xticks(minor=not is_ticks_major) for aii in axes]

    max_nbins = max([len(tick) for tick in ticks])

    # Get upper and lower bounds of each axis
    bounds = [aii.get_ylim() for aii in axes]

    new_ticks = [
        np.linspace(
            ticks[ii][0],
            ticks[ii][0] + (ticks[ii][1] - ticks[ii][0]) * (max_nbins - 1),
            max_nbins,
        )
        for ii in range(n_ax)
    ]

    # find the lower bound
    idx_l = 0
    for i in range(len(new_ticks[0])):
        if any((new_ticks[jj][i] > bounds[jj][0] for jj in range(n_ax))):
            idx_l = i - 1
            break

    # find the upper bound
    idx_r = 0
    for i in range(len(new_ticks[0])):
        if all((new_ticks[jj][i] > bounds[jj][1] for jj in range(n_ax))):
            idx_r = i
            break

    # trim tick lists by bounds
    new_ticks = [tii[idx_l : idx_r + 1] for tii in new_ticks]

    # set ticks for each axis
    for axii, tii in zip(axes, new_ticks):
        if is_y_axis:
            axii.set_yticks(tii)
        else:
            axii.set_xticks(tii)

    return new_ticks


def align_x_axes_on_values(
    axes: List[Axes],
    align_values: Optional[List[float]] = None,
    is_ticks_major: bool = True,
) -> List[Any]:
    """
    Align the ticks of multiple x axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.
    Source :
    https://stackoverflow.com/questions/26752464/how-do-i-align-gridlines-for-two-y-axis-scales-using-matplotlib

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose xaxis ticks are to be aligned.
    align_values : None or list/tuple
        If not None, should be a list/tuple of floats with same length as
        <axes>. Values in <align_values> define where the corresponding
        axes should be aligned up. E.g. [0, 100, -22.5] means the 0 in
        axes[0], 100 in axes[1] and -22.5 in axes[2] would be aligned up.
        If None, align (approximately) the lowest ticks in all axes.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    return _align_axes_on_values(axes, False, align_values, is_ticks_major)


def align_y_axes_on_values(
    axes: List[Axes],
    align_values: Optional[List[float]] = None,
    is_ticks_major: bool = True,
) -> List[Any]:
    """
    Align the ticks of multiple y axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.
    Source :
    https://stackoverflow.com/questions/26752464/how-do-i-align-gridlines-for-two-y-axis-scales-using-matplotlib

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose yaxis ticks are to be aligned.
    align_values : None or list/tuple
        If not None, should be a list/tuple of floats with same length as
        <axes>. Values in <align_values> define where the corresponding
        axes should be aligned up. E.g. [0, 100, -22.5] means the 0 in
        axes[0], 100 in axes[1] and -22.5 in axes[2] would be aligned up.
        If None, align (approximately) the lowest ticks in all axes.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    return _align_axes_on_values(axes, True, align_values, is_ticks_major)


def _align_axes_on_values(
    axes: List[Axes],
    is_y_axis: bool = True,
    align_values: Optional[List[float]] = None,
    is_ticks_major: bool = True,
) -> List[Any]:
    """
    Align the ticks of multiple axes.

    A new sets of ticks are computed for each axis in <axes> but with equal
    length.
    Source :
    https://stackoverflow.com/questions/26752464/how-do-i-align-gridlines-for-two-y-axis-scales-using-matplotlib

    Parameters
    ----------
    axes : List[Axes]
        List of axes objects whose x/y-axis ticks are to be aligned.
    is_y_axis:
        Whether to perform the alignment on the y-axis. If False, perform it on the
        x axis. The default is True.
    align_values : None or list/tuple
        If not None, should be a list/tuple of floats with same length as
        <axes>. Values in <align_values> define where the corresponding
        axes should be aligned up. E.g. [0, 100, -22.5] means the 0 in
        axes[0], 100 in axes[1] and -22.5 in axes[2] would be aligned up.
        If None, align (approximately) the lowest ticks in all axes.
    is_ticks_major: bool, optional
        Whether to consider only major ticks. The default is True.

    Returns
    -------
        new_ticks (list): a list of new ticks for each axis in <axes>.
    """
    n_ax = len(axes)
    if is_y_axis:
        ticks = [aii.get_yticks(minor=not is_ticks_major) for aii in axes]
    else:
        ticks = [aii.get_xticks(minor=not is_ticks_major) for aii in axes]

    if align_values is None:
        aligns = [ticks[ii][0] for ii in range(n_ax)]
    else:
        if len(align_values) != n_ax:
            raise ValueError(
                "Length of <axes> doesn't equal that " "of <align_values>."
            )
        aligns = align_values

    # Get upper and lower bounds of each axis
    if is_y_axis:
        bounds = [aii.get_ylim() for aii in axes]
    else:
        bounds = [aii.get_xlim() for aii in axes]

    # align at some points
    ticks_align = [ticks[ii] - aligns[ii] for ii in range(n_ax)]

    # scale the range to 1-100
    ranges = [tii[-1] - tii[0] for tii in ticks]
    lgs = [-np.log10(rii) + 2.0 for rii in ranges]
    igs = [np.floor(ii) for ii in lgs]
    log_ticks = [ticks_align[ii] * (10.0 ** igs[ii]) for ii in range(n_ax)]

    # put all axes ticks into a single array,
    # then compute new ticks for all
    comb_ticks = np.concatenate(log_ticks)
    comb_ticks.sort()
    locator = plt.MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 3, 4, 5, 8, 10])
    new_ticks = locator.tick_values(comb_ticks[0], comb_ticks[-1])
    new_ticks = [new_ticks / 10.0 ** igs[ii] for ii in range(n_ax)]
    new_ticks = [new_ticks[ii] + aligns[ii] for ii in range(n_ax)]

    # find the lower bound
    idx_l = 0
    for i in range(len(new_ticks[0])):
        if any((new_ticks[jj][i] > bounds[jj][0] for jj in range(n_ax))):
            idx_l = i - 1
            break

    # find the upper bound
    idx_r = 0
    for i in range(len(new_ticks[0])):
        if all((new_ticks[jj][i] > bounds[jj][1] for jj in range(n_ax))):
            idx_r = i
            break

    # trim tick lists by bounds
    new_ticks = [tii[idx_l : idx_r + 1] for tii in new_ticks]

    # set ticks for each axis
    for axii, tii in zip(axes, new_ticks):
        if is_y_axis:
            axii.set_yticks(tii)
        else:
            axii.set_xticks(tii)

    return new_ticks


def make_x_axes_symmetric_zero_centered(axes: List[Axes]) -> None:
    """
    Make all given x axes symmetric in zero.

    Always put 0 in the middle of the graph for all x axes.

    Parameters
    ----------
    axes : List[Axes]
        List of axes to adjust.

    Returns
    -------
    None.

    """
    max_lims = np.max(np.abs(np.array([ax.get_xlim() for ax in axes])), axis=1)
    for i, ax in enumerate(axes):
        ax.set_xlim([-max_lims[i], max_lims[i]])


def make_y_axes_symmetric_zero_centered(axes: List[Axes]) -> None:
    """
    Make all given y axes symmetric in zero.

    Always put 0 in the middle of the graph for all y axes.

    Parameters
    ----------
    axes : List[Axes]
        List of axes to adjust.

    Returns
    -------
    None.

    """
    max_lims = np.max(np.abs(np.array([ax.get_ylim() for ax in axes])), axis=1)
    for i, ax in enumerate(axes):
        ax.set_ylim([-max_lims[i], max_lims[i]])


def add_xaxis_twin_as_date(
    ax: Axes,
    first_date: datetime,
    time_units: Literal["days", "d", "months", "m", "years", "y"] = "days",
    time_format: str = "%d-%m-%Y",
    spine_outward_position: float = 48.0,
    date_rotation: float = 15.0,
) -> Axes:
    """
    Add dates to an already existing axis.

    The dates are creating frm a first day axis (numbered from x to n),
    taking the time series first date as the starting date.

    Parameters
    ----------
    ax: Axes
        The axis for which to add a twin xaxis.
    first_date : datetime
        Date associated with the first data point.
    time_units : Literal["days", "d", "months", "m", "years", "y"], optional
        Unit of time between two data points. The default is "days".
    time_format : str, optional
        Time format for display. The default is "%d-%m-%Y".
    spine_outward_position : float, optional
        The spine is placed out from the data area by the specified number of points
        (Negative values place the spine inwards). The default is 48.0.
    date_rotation : float, optional
        Rotation angle in degrees to apply to ticks labels
        (in degrees, counterclockwise). The default is 15.0.

    Returns
    -------
    Axes
        The created date xaxis.

    """
    # Creation of a second x axis
    ax2: Axes = ax.twiny()

    # Get the values at the ticks in the first x axis
    ax1_xticks = ax.get_xticks()
    # Create an empty list of the future ticks for the second x-axis
    ax2_xticklabels = []
    # Fill the list
    if time_units in ["days", "d"]:
        for value in ax1_xticks:
            ax2_xticklabels.append(
                (first_date + timedelta(days=float(value))).strftime(time_format)
            )
    elif time_units in ["months", "m"]:
        for value in ax1_xticks:
            ax2_xticklabels.append(
                (first_date + relativedelta(months=int(value))).strftime(time_format)
            )
    elif time_units in ["years", "y"]:
        for value in ax1_xticks:
            ax2_xticklabels.append(
                (first_date + relativedelta(years=int(value))).strftime(time_format)
            )
    else:
        raise ValueError(
            r"time_units should be in ['days', 'd', 'months', 'm', 'years', 'y']"
        )

    ax2.set_xticks(ax1_xticks)
    ax2.set_xbound(ax.get_xbound())
    ax2.set_xticklabels(ax2_xticklabels)

    ax.xaxis.set_ticks_position("bottom")
    ax2.xaxis.set_ticks_position("bottom")
    ax2.spines["bottom"].set_position(("outward", spine_outward_position))

    for tick in ax2.get_xticklabels():
        tick.set_rotation(date_rotation)

    return ax2


def add_letter_to_frames(axes: Sequence[Axes]) -> None:
    """
    Add a letter at the top left hand corner of the frame of the given axes.

    If more than 26 frames are provided, the letters are complemented by a numeral
    suffix, e.g., a-1, b-1, c-1, ... z-1, a-2, b-2, ...

    Parameters
    ----------
    axes : Sequence[Axes]
        Sequence of axes to label.
    """
    # dict of letters
    d = dict(enumerate(string.ascii_lowercase, 1))

    if len(axes) <= 26:

        def _get_letter(_i: int) -> str:
            return d[_i + 1]

    else:  # need to add numbers to letters

        def _get_letter(_i: int) -> str:
            return f"{d[_i%26 + 1]}-{_i//26+1}"

    for i, ax in enumerate(axes):
        ax.text(
            0.0,
            1.0,
            _get_letter(i),
            color="k",
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontweight="bold",
            bbox=dict(facecolor="white", edgecolor="k", pad=5.0),
        )
