"""Provide some tools for 2D plots."""

import copy
import warnings
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

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


def _get_vmin_vmax(
    data_list: List[npt.NDArray[np.float64]],
    is_symmetric_cbar: bool,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Get vmin and vmax for the color bar scaling.

    Parameters
    ----------
    data_list : List[np.ndarray]
        List of arrays containing the data.
    is_symmetric_cbar : bool
        Does the scale need to be symmetric and centered to zero. The default is False.
    vmin: Optional[float]
        Minimum value for the scale. If not provided, it is automatically derived
        from the data. The default is None.
    vmax: Optional[float]
        Maximum value for the scale. If not provided, it is automatically derived
        from the data. The default is None.
    """

    if vmin is None:
        vmin = np.nanmin([np.nanmin(data) for data in data_list])
    if vmax is None:
        vmax = np.nanmax([np.nanmax(data) for data in data_list])
    if is_symmetric_cbar:
        abs_norm = max(abs(vmin), abs(vmax))
        vmin = -abs_norm
        vmax = abs_norm
    return vmin, vmax


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


def _norm_data_and_cbar(
    images: List[AxesImage],
    data: List[npt.NDArray[np.float64]],
    _imshow_kwargs: Dict[str, Any],
    is_symmetric_cbar: bool,
) -> None:
    """
    Apply a proper scaling to the colorbar based on data and user provided norm.

    Parameters
    ----------
    images_dict : Dict[str, AxesImage]
        Dict of images for which to scale the colorbar.
    data_list : Dict[str, npt.NDArray[np.float64]]
        Dict of arrays containing the data.
    _imshow_kwargs: Dict[str, Any]
        Keywords arguments for imshow.
    is_symmetric_cbar : bool
        Does the scale need to be symmetric and centered to zero. The default is False.
    """
    norm: colors.Normalize = _imshow_kwargs.get("norm", colors.Normalize())
    if isinstance(norm, colors.LogNorm) and is_symmetric_cbar:
        warnings.warn(
            "You used a LogNorm norm instance which is incompatible with a"
            " symmetric colorbar. Symmetry is ignored. Use SymLogNorm for"
            " symmetrical logscale color bar.",
            UserWarning,
        )
        is_symmetric_cbar = False

    vmin, vmax = _get_vmin_vmax(
        data,
        is_symmetric_cbar,
        norm.vmin if norm.vmin is not None else _imshow_kwargs.get("vmin"),
        norm.vmax if norm.vmax is not None else _imshow_kwargs.get("vmax"),
    )
    norm.vmin = vmin
    norm.vmax = vmax
    for im in images:
        im.set_norm(norm)


def multi_imshow(
    axes: Sequence[Axes],
    fig: Union[Figure, SubFigure],
    data: Dict[str, npt.NDArray[np.float64]],
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    imshow_kwargs: Optional[Dict[str, Any]] = None,
    cbar_kwargs: Optional[Dict[str, Any]] = None,
    is_symmetric_cbar: bool = False,
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
    is_symmetric_cbar : bool, optional
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
        ax.set_title(label, fontweight="bold")
        if xlabel is not None:
            ax.set_xlabel(xlabel, fontweight="bold")
        if ylabel is not None:
            ax.set_ylabel(ylabel, fontweight="bold")

        # norm both data and colobar
        _norm_data_and_cbar(
            list(images_dict.values()),
            list(data.values()),
            _imshow_kwargs,
            is_symmetric_cbar,
        )

    cbar: Colorbar = fig.colorbar(list(images_dict.values())[0], **_cbar_kwargs)
    if cbar_title is not None:
        cbar.ax.get_yaxis().labelpad = 20
        cbar.ax.set_ylabel(cbar_title, rotation=270)

    return cbar
