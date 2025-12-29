"""
Utilities for matplotlib.
"""

import base64
import re
import string
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, TypeVar, Union

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from dateutil.relativedelta import relativedelta
from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from typing_extensions import Literal

NDArrayFloat = npt.NDArray[np.float64]
# pylint: disable=C0103 # does not confrom to snake case naming style
# pylint: disable=R0913 # too many arguments
# pylint: disable=R0914 # too many local variables

_Object = TypeVar("_Object", bound=object)


def object_or_object_sequence_to_list(
    _input: Union[_Object, Sequence[_Object]],
) -> List[_Object]:
    """Convert a singleton or an iterable of this object to a list of object."""
    if isinstance(_input, Iterable):
        return [item for item in _input]
    return [_input]


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
    start_indices_at_one: bool = True,
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
    start_indices_at_one: bool
        Whether to start indices at one or ay zero. The default is True, i.e., start at
        one.

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

    start_index: int = 1 if start_indices_at_one else 0

    # Iterate the patterns
    for m in pattern.finditer(input_text):
        res = m.groupdict()
        frame_format = res.get("frame_format")
        if frame_format == r"svg+xml":
            frame_format = "svg"
        path = _target_path.joinpath(
            f"frame{int(res.get('frame_index')) + start_index:0>7d}.{frame_format}"
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


def _find_new_ticks(
    new_ticks: List[NDArrayFloat],
    bounds: Sequence[Tuple[float, float]],
    n_ax: int,
) -> List[NDArrayFloat]:
    # find the lower bound
    idx_lb = 0
    for i in range(len(new_ticks[0])):
        if any((new_ticks[jj][i] > bounds[jj][0] for jj in range(n_ax))):
            idx_lb = i - 1
            break

    # find the upper bound
    idx_ub = 0
    for i in range(len(new_ticks[0])):
        if all((new_ticks[jj][i] > bounds[jj][1] for jj in range(n_ax))):
            idx_ub = i
            break

    return [tii[idx_lb : idx_ub + 1] for tii in new_ticks]


def align_and_set_new_ticks(
    axes: List[Axes],
    new_ticks: List[NDArrayFloat],
    bounds: Sequence[Tuple[float, float]],
    n_ax: int,
    is_y_axis: bool,
) -> List[NDArrayFloat]:
    # find the lower and uppers bounds
    new_ticks = _find_new_ticks(new_ticks, bounds, n_ax)

    # set ticks for each axis
    for axii, tii in zip(axes, new_ticks):
        if is_y_axis:
            axii.set_yticks(tii)
        else:
            axii.set_xticks(tii)

    return new_ticks


def _align_axes(
    axes: List[Axes], is_ticks_major: bool = True, is_y_axis: bool = True
) -> List[NDArrayFloat]:
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
    return align_and_set_new_ticks(axes, new_ticks, bounds, n_ax, is_y_axis)


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
) -> List[NDArrayFloat]:
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
            raise ValueError("Length of <axes> doesn't equal that of <align_values>.")
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

    return align_and_set_new_ticks(axes, new_ticks, bounds, n_ax, is_y_axis)


def _get_min_abs_lims(
    axes: List[Axes], min_abs_lims: Optional[List[float]] = None
) -> NDArrayFloat:
    if min_abs_lims is not None:
        if len(min_abs_lims) != len(axes):
            raise ValueError(
                f"The number of axes ({len(axes)}) and of absolute "
                f"limits `min_abs_lims` ({len(min_abs_lims)}) should be the same!"
            )
        return np.abs(min_abs_lims)
    return np.repeat([np.nan], len(axes))


def _make_axes_symmetric_zero_centered(
    axes: Union[_AxesBase, List[_AxesBase]],
    is_yaxis: bool,
    min_abs_lims: Optional[Union[float, List[float]]] = None,
) -> None:
    _axes = object_or_object_sequence_to_list(axes)
    _min_abs_lims = _get_min_abs_lims(
        _axes,
        (
            object_or_object_sequence_to_list(min_abs_lims)
            if min_abs_lims is not None
            else None
        ),
    )

    def get_lim(ax: _AxesBase) -> Tuple[float, float]:
        if is_yaxis:
            return ax.get_ylim()
        return ax.get_xlim()

    max_lims: NDArrayFloat = np.nanmax(
        [
            np.max(np.abs(np.array([get_lim(ax) for ax in _axes])), axis=1),
            _min_abs_lims,
        ],
        axis=0,
    )

    def set_symlim(ax: Axes, lim: float) -> None:
        if is_yaxis:
            ax.set_ylim(-lim, lim)
        else:
            ax.set_xlim(-lim, lim)

    for i, ax in enumerate(_axes):
        set_symlim(ax, max_lims[i])


def make_x_axes_symmetric_zero_centered(
    axes: Union[Axes, List[Axes]], min_xlims: Optional[Union[float, List[float]]] = None
) -> None:
    """
    Make x-axis symmetric in zero for all provided axes

    Always put 0 in the middle of the graph for all x axes.

    Parameters
    ----------
    axes : Union[Axes, List[Axes]]
        Axis or list of axes to adjust.
    min_xlims: Optional[Union[float, List[float]]]

        .. versionadded:: 1.2

        Minimum xlim for each axis. If data range from -2.0 to 5.0, and `min_xlims` is
        1.0, then the limits would be [-5.0, 5.0], but if `min_xlims` is 10.0 or
        -10.0, then, the limits would be [-10.0, 10.0]. If None, then it is ignored.
        The provided list should have the same number of elements as `axes`.
        By default None.

    Returns
    -------
    None.

    """
    _make_axes_symmetric_zero_centered(axes, False, min_xlims)


def make_y_axes_symmetric_zero_centered(
    axes: Union[_AxesBase, List[_AxesBase]],
    min_ylims: Optional[Union[float, List[float]]] = None,
) -> None:
    """
    Make y-axis symmetric in zero for all provided axes.

    Always put 0 in the middle of the graph for all y axes.

    Parameters
    ----------
    axes : Union[Axes, List[Axes]]
        Axis or list of axes to adjust.
    min_ylims: Optional[Union[float, List[float]]]

        .. versionadded:: 1.2

        Minimum ylim for each axis. If data range from -2.0 to 5.0, and `min_ylims` is
        1.0, then the limits would be [-5.0, 5.0], but if `min_ylims` is 10.0 or
        -10.0, then, the limits would be [-10.0, 10.0]. The provided list should have
        the same number of elements as `axes`. If None, then it is ignored.
        By default None.

    Returns
    -------
    None.

    """
    _make_axes_symmetric_zero_centered(axes, True, min_ylims)


def ticklabels_to_datetime(
    ax: _AxesBase,
    initial_datetime: datetime,
    is_y_axis: bool,
    step: relativedelta,
    format: str = "%d-%m-%Y",
    rotation_degrees: float = 15.0,
) -> None:
    """
    Convert float ticklabels to datetime.

    .. versionadded:: 1.2

    Parameters
    ----------
    ax: Axes
        The axis for which the transformation is applied.
    initial_datetime : datetime
        Date associated with the first data point.
    is_y_axis : bool
        Whether to apply the transformation to the y axis.
    initial_datetime : datetime
        Date associated with the first data point.
    step: relativedelta
        Unit of time between two data points. The default is "days".
    format : str, optional
        Time format for display. The default is "%d-%m-%Y".
    rotation_degrees : float, optional
        Rotation angle in degrees to apply to ticks labels
        (in degrees, counterclockwise). The default is 15.0.
    """

    # Compute the datetimes
    def _get_ticks():
        if is_y_axis:
            return ax.get_yticks()
        return ax.get_xticks()

    ticklabels = [
        (initial_datetime + step * tl).strftime(format) for tl in _get_ticks()
    ]

    # Set the new labels
    if is_y_axis:
        # it has a tendency to change the axis limits so we artificially maintain it
        lims = ax.get_ylim()
        # fix the ticks before using setticklabels otherwise a warning is raised
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels(ticklabels)
        ax.set_ylim(lims)
    else:
        lims = ax.get_xlim()
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels(ticklabels)
        ax.set_xlim(lims)

    # Rotate the labels to avoid overlapping

    def _get_ticklabels():
        if is_y_axis:
            return ax.get_yticklabels()
        return ax.get_xticklabels()

    for tick in _get_ticklabels():
        if rotation_degrees < 0:
            rotation_degrees += 360
        tick.set_rotation(rotation_degrees)


def add_twin_axis_as_datetime(
    ax: _AxesBase,
    initial_datetime: datetime,
    step: relativedelta,
    format: str = "%d-%m-%Y",
    rotation_degrees: float = 15.0,
    spine_outward_position: float = 48.0,
    position: Literal["top", "bottom", "left", "right"] = "bottom",
    is_hide_opposed_tick_labels: bool = True,
) -> _AxesBase:
    """
    Add dates to an already existing axis.

    .. versionadded:: 1.2

    The dates are creating from a first day axis (numbered from x to n),
    taking the time series first date as the starting date.

    Parameters
    ----------
    ax: Axes
        The axis for which to add a twin xaxis.
    initial_datetime : datetime
        Date associated with the first data point.
    step: relativedelta
        Unit of time between two data points. The default is "days".
    format : str, optional
        Time format for display. The default is "%d-%m-%Y".
    rotation_degrees : float, optional
        Rotation angle in degrees to apply to ticks labels
        (in degrees, counterclockwise). The default is 15.0.
    spine_outward_position : float, optional
        The spine is placed out from the data area by the specified number of points
        (Negative values place the spine inwards). The default is 48.0.
    position: Literal["top", "bottom", "left", "right"]
        Position of the new axis.

    Returns
    -------
    Axes
        The created date xaxis.

    """
    is_y_axis: bool = {"top": False, "bottom": False, "left": True, "right": True}[
        position
    ]

    # Creation of a second x or y axis
    if is_y_axis:
        ax2: _AxesBase = ax.twinx()
    else:
        ax2 = ax.twiny()

    # Impose the same ticks
    if is_y_axis:
        ax2.set_yticks(ax.get_yticks())
        ax2.set_ybound(*ax.get_ybound())
    else:
        ax2.set_xticks(ax.get_xticks())
        ax2.set_xbound(*ax.get_xbound())

    if is_y_axis:
        ax2.yaxis.set_ticks_position(position)
    else:
        ax2.xaxis.set_ticks_position(position)

    # Apply a shift
    ax2.spines[position].set_position(("outward", spine_outward_position))

    ticklabels_to_datetime(
        ax2,
        initial_datetime,
        is_y_axis,
        step,
        format,
        rotation_degrees,
    )

    return ax2


def add_xaxis_twin_as_date(
    ax: Axes,
    first_date: datetime,
    time_units: Literal["days", "d", "months", "m", "years", "y"] = "days",
    time_format: str = "%d-%m-%Y",
    spine_outward_position: float = 48.0,
    date_rotation: float = 15.0,
    position: Literal["top", "bottom"] = "bottom",
) -> Axes:
    """
    Add dates to an already existing axis.

    .. deprecated:: 1.2
        Use :func:`add_twin_axis_as_datetime` instead.

    The dates are creating from a first day axis (numbered from x to n),
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
    raise NotImplementedError(
        '"add_xaxis_twin_as_date" was removed in '
        'version 1.2, use "add_twin_axis_as_datetime" instead!'
    )


def add_letter_to_frames(axes: Sequence[Axes], zorder: int = 10) -> None:
    """
    Add a letter at the top left hand corner of the frame of the given axes.

    If more than 26 frames are provided, the letters are complemented by a numeral
    suffix, e.g., a-1, b-1, c-1, ... z-1, a-2, b-2, ...

    Parameters
    ----------
    axes : Sequence[Axes]
        Sequence of axes to label.
    zorder: int
        Drawing order for axes is patches, lines, text. The default is 10.
    """
    # dict of letters
    d = dict(enumerate(string.ascii_lowercase, 1))

    if len(axes) <= 26:

        def _get_letter(_i: int) -> str:
            return d[_i + 1]

    else:  # need to add numbers to letters

        def _get_letter(_i: int) -> str:
            return f"{d[_i % 26 + 1]}-{_i // 26 + 1}"

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
            zorder=zorder,
            family="monospace",
        )
