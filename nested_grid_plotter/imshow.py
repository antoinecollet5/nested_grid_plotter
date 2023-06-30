"""Provide some tools for 2D plots."""

import copy
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import numpy.typing as npt
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure, SubFigure
from matplotlib.image import AxesImage

# pylint: disable=C0103 # does not confrom to snake case naming style
# pylint: disable=R0913 # too many arguments
# pylint: disable=R0914 # too many local variables


def _apply_default_imshow_kwargs(
    imshow_kwargs: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Apply default values to the given imshow kwargs dictionary."""
    _imshow_kwargs: dict[str, Any] = {
        "interpolation": "nearest",
        "cmap": "bwr",
        "aspect": "auto",
        "origin": "lower",
    }
    if imshow_kwargs is not None:
        _imshow_kwargs.update(imshow_kwargs)
    if not any(v in _imshow_kwargs for v in ["vmin", "vmax", "norm"]):
        _imshow_kwargs.update({"norm": colors.Normalize()})
    return _imshow_kwargs


def _apply_default_colorbar_kwargs(
    colorbar_kwargs: Optional[Dict[str, Any]], axes: Sequence[Axes]
) -> Dict[str, Any]:
    """Apply default values to the given colorbar kwargs dictionary."""
    _colorbar_kwargs: dict[str, Any] = {
        "orientation": "vertical",
        "aspect": 20,
        "ax": np.array(axes),  # Make sure to have a  numpy array
    }
    if colorbar_kwargs is not None:
        _colorbar_kwargs.update(colorbar_kwargs)
    return _colorbar_kwargs


def add_2d_grid(
    ax: Axes, nx: int, ny: int, kwargs: Optional[Dict[str, Any]] = None
) -> None:
    """
    Add a grid to the.

    Parameters
    ----------
    ax : Axes
        The axis to which add a grid.
    nx : int
        Number of vertical bars.
    ny : int
        Number of horizontal bars.
    kwargs : Optional[Dict[str, Any]], optional
        Optional arguments for vlines and hlines. The default is None.

    Returns
    -------
    None.

    """
    _kwargs = {"color": "grey", "linewidths": 0.5}
    if kwargs is not None:
        _kwargs.update(kwargs)
    ax.vlines(
        x=np.arange(0, nx) + 0.5,
        ymin=np.full(nx, 0) - 0.5,
        ymax=np.full(nx, ny) - 0.5,
        **_kwargs,
    )
    ax.hlines(
        y=np.arange(0, ny) + 0.5,
        xmin=np.full(ny, 0) - 0.5,
        xmax=np.full(ny, nx) - 0.5,
        **_kwargs,
    )


def _scale_cbar(
    images: List[AxesImage],
    data_list: List[npt.NDArray[np.float64]],
    is_symetric_cbar: bool,
    is_log: bool = False,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> None:
    """
    Scale the color bar span to the input data.

    Parameters
    ----------
    images : List[AxesImage]
        List of images for which to scale the colorbar.
    data_list : List[np.ndarray]
        List of arrays containing the data.
    is_symetric_cbar : bool
        Does the scale need to be symmetric and centered to zero. The default is False.
    is_log : bool, optional
        Does the scale need to be logarithmic. The default is False.
    vmin: Optional[float]
        Minimum value for the scale. If not provided, it is automatically derived
        from the data. The default is None.
    vmax: Optional[float]
        Maximum value for the scale. If not provided, it is automatically derived
        from the data. The default is None.
    """
    # Find the min and max of all colors for use in setting the color scale.
    if vmin is None:
        vmin = np.nanmin([np.nanmin(data) for data in data_list])
    if vmax is None:
        vmax = np.nanmax([np.nanmax(data) for data in data_list])
    if is_symetric_cbar:
        abs_norm = max(abs(vmin), abs(vmax))
        vmin = -abs_norm
        vmax = abs_norm
    if is_log:
        norm = colors.LogNorm(vmin=vmin, vmax=vmax)
    else:
        norm = colors.Normalize(vmin=vmin, vmax=vmax)
    for im in images:
        im.set_norm(norm)


def _check_axes_and_data_consistency(
    axes: Sequence[Axes], data: Dict[str, npt.NDArray[np.float64]]
) -> None:
    """
    Check that the number of axes and keys in data are the same.

    Parameters
    ----------
    axes : Sequence[Axes]
        List of axes.
    data : Dict[str, npt.NDArray[np.float64]]
        Dictionary of data arrays.

    Raises
    ------
    ValueError
        If the number of axes and keys in data are not the same.

    Returns
    -------
    None
    """
    _n_data: int = len(data.values())
    _n_axes: int = len(axes)
    if _n_data != _n_axes:
        raise ValueError(
            f"The number of axes ({_n_axes}), does not match the number "
            f"of data ({_n_data})!"
        )


def multi_imshow(
    axes: Sequence[Axes],
    fig: Union[Figure, SubFigure],
    data: Dict[str, npt.NDArray[np.float64]],
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    imshow_kwargs: Optional[Dict[str, Any]] = None,
    cbar_kwargs: Optional[Dict[str, Any]] = None,
    is_symetric_cbar: bool = False,
    cbar_title: Optional[str] = None,
) -> Colorbar:
    """
    Plot multiple 2D field with imshow using a shared and scaled colorbar.

    Parameters
    ----------
    axes : Sequence[Axes]
        Sequence of axes on which to plot the given data.
    fig : Figure
        The figure on which to plot the data. This is useful to position correctly
        the colorbar.
    data : Dict[str, npt.NDArray[np.float64]]
        Dictionary of data arrays. Key are used as axis title.
    xlabel : Optional[str], optional
        Label to apply to all xaxes. The default is None.
    ylabel : Optional[str], optional
        Label to apply to all yaxes. The default is None.
    imshow_kwargs : Optional[Dict[str, Any]], optional
        Optional arguments for `plt.imshow`. The default is None.
    cbar_kwargs : Optional[Dict[str, Any]], optional
        DESCRIPTION. The default is None.
    is_symetric_cbar : bool, optional
        Does the scale need to be symmetric and centered to zero. The default is False.
    cbar_title : Optional[str], optional
        Label to give to the colorbar. The default is None.

    Raises
    ------
    ValueError
        If the given data arrays do not have the required dimensionality (3).

    Returns
    -------
    Colorbar
        The color bar is returned so it can be further customized.

    """
    # The number of ax_name and data provided should be the same:
    _check_axes_and_data_consistency(axes, data)

    # Add some default values for imshow and colorbar
    _imshow_kwargs: Dict[str, Any] = _apply_default_imshow_kwargs(imshow_kwargs)
    _cbar_kwargs: Dict[str, Any] = _apply_default_colorbar_kwargs(cbar_kwargs, axes)

    images_dict: Dict[str, AxesImage] = {}
    for j, (label, values) in enumerate(data.items()):
        ax: Axes = axes[j]
        if not len(values.shape) == 2:
            raise ValueError(
                f'The given data for "{label}" has dimension {len(values.shape)} '
                "whereas it should be two dimensional!"
            )

        # Need to transpose because the dimensions (M, N) define the rows and
        # columns
        # Also, need to copy the _imshow_kwargs to avoid its update. Otherwise the
        # colorbar scaling does not work properly
        images_dict[label] = ax.imshow(values.T, **copy.deepcopy(_imshow_kwargs))

        ax.label_outer()
        ax.set_title(label, style="italic", fontweight="bold")
        ax.set_title(label, style="italic", fontweight="bold")
        if xlabel is not None:
            ax.set_xlabel(xlabel, fontweight="bold")
        if ylabel is not None:
            ax.set_ylabel(ylabel, fontweight="bold")

    norm: Optional[colors.Normalize] = _imshow_kwargs.get("norm")
    if norm is not None:
        vmin: Optional[float] = norm.vmin
        vmax: Optional[float] = norm.vmax
        if isinstance(norm, colors.LogNorm):
            _scale_cbar(
                list(images_dict.values()),
                list(data.values()),
                False,
                is_log=True,
                vmin=vmin,
                vmax=vmax,
            )
        elif isinstance(_imshow_kwargs.get("norm"), colors.Normalize):
            _scale_cbar(
                list(images_dict.values()),
                list(data.values()),
                is_symetric_cbar,
                vmin=vmin,
                vmax=vmax,
            )

    cbar: Colorbar = fig.colorbar(list(images_dict.values())[0], **_cbar_kwargs)
    if cbar_title is not None:
        cbar.ax.get_yaxis().labelpad = 20
        cbar.ax.set_ylabel(cbar_title, rotation=270)

    return cbar
