"""Offer a field plotter."""

import copy
import warnings
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Union

import numpy as np
import numpy.typing as npt
from matplotlib.animation import FuncAnimation
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure, SubFigure
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.text import Text

from nested_grid_plotter.base_plotter import NestedGridPlotter
from nested_grid_plotter.imshow import (
    _apply_default_colorbar_kwargs,
    _apply_default_imshow_kwargs,
    _check_axes_and_data_consistency,
    _norm_data_and_cbar,
)

# pylint: disable=C0103 # does not confrom to snake case naming style
# pylint: disable=R0913 # too many arguments
# pylint: disable=R0914 # too many local variables

# Define some types for numpy
NDArrayFloat = npt.NDArray[np.float64]
NDArrayInt = npt.NDArray[np.int64]


def _get_nb_frames(nb_frames: Optional[int], nb_steps: int) -> int:
    """
    Get the correct number of frames.

    Parameters
    ----------
    nb_frames : Optional[int]
        Number of frames to plot. If None, then the number of steps is used.
    nb_steps : int
        Number of steps (data arrays available for plot).

    Returns
    -------
    int
        The correct number of frames.

    Raises
    ------
    warnings.warn
        If the nb_frames required exceeds the number of steps.
    """
    if nb_frames is None:
        return nb_steps
    if nb_frames > nb_steps:
        warnings.warn(
            UserWarning(
                f"The nb_frames ({nb_frames}) required exceeds the number of steps"
                f" available (last dimension of arrays = {nb_steps})!"
                " Some images will be repeated."
            )
        )
    return nb_frames


class AnimatedPlotter(NestedGridPlotter):
    """Nestedgrid plotter with embedded animation support."""

    _animation: Optional[FuncAnimation]

    def __init__(
        self,
        fig_params: Optional[Dict[str, Any]] = None,
        subfigs_params: Optional[Dict[str, Any]] = None,
        subplots_mosaic_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initiate the instance.

        Parameters
        ----------
        fig_params : Optional[Dict[str, Any]], optional
            See  :class:`NestedGridPlotter` for other possible arguments.
            The default is None.
        subfigs_params : Optional[Dict[str, Any]], optional
            DESCRIPTION. The default is None.
        subplots_mosaic_params : Optional[Dict[str, Any]], optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None
        """
        _fig_params = dict(constrained_layout=True)
        if fig_params is not None:
            _fig_params.update(fig_params)

        super().__init__(_fig_params, subfigs_params, subplots_mosaic_params)
        # self.fig.patch.set_facecolor("w")
        self.init_animations_list: List[Callable] = []
        self.animations_list: List[Callable] = []
        self.animation = None

    @property
    def animation(self) -> FuncAnimation:
        """Get the animation or raise an attribute error if not defined."""
        if self._animation is None:
            raise AttributeError("No animation as been defined !")
        return self._animation

    @animation.setter
    def animation(self, animation: Optional[FuncAnimation]) -> None:
        self._animation = animation

    def _init_animate(self) -> List[Union[Line2D, AxesImage]]:
        """Only required for blitting to give a clean slate."""
        return [f for f_list in self.init_animations_list for f in f_list()]

    def _animate(self, i) -> List[Union[Line2D, AxesImage]]:
        """Update the data of the plot."""
        return [f for f_list in self.animations_list for f in f_list(i)]

    def animate(self, nb_frames: int, blit: bool = True) -> FuncAnimation:
        """
        Animate the plot.

        Parameters
        ----------
        nb_frames : int
            The number of frames to consider for the animation.
        blit: bool, optional
            Whether blitting is used to optimize drawing. Note: when using blitting,
            any animated artists will be drawn according to their zorder; however,
            they will be drawn on top of any previous artists, regardless of their
            zorder. The default is True.

        Returns
        -------
        animation.FuncAnimation
            The animation.

        """
        # plt.close(self.fig)
        self.animation = FuncAnimation(
            self.fig,
            self._animate,
            init_func=self._init_animate,
            frames=range(nb_frames),
            interval=1,
            blit=blit,
            repeat=False,
        )
        return self.animation

    def plot_animated_text(
        self, ax: Axes, x: float, y: float, s: Sequence[str], **kwargs: Any
    ) -> None:
        """
        Add a text animation to the given axis.

        Parameters
        ----------
        ax : Axes
            Axis to which add the text.
        x : float
            x position of the text.
        y : float
            y position of the text.
        s : Sequence[str]
            Sequence of text value to display.
        **kwargs : Dict[str, Any]
            Optional arguments for the class:`Text`.

        Returns
        -------
        None

        """
        txt: Text = ax.text(x, y, s[0], **kwargs)

        def _animate(frame: int) -> List[Text]:
            """Update the text value."""
            txt.set_text(s[frame])
            return [
                txt,
            ]

        # self.init_animations_list.append(_init)
        self.animations_list.append(_animate)

    def animated_multi_plot(
        self,
        ax_name: str,
        data: Dict[str, Dict[str, Any]],
        nb_frames: Optional[int] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
    ) -> None:
        """
        Plot a 1D animated curves.

        The number of frames can be determined automatically from the data.

        Parameters
        ----------
        ax_name : str
            Name of the axis on which to plot the animation.
        data : Dict[str, Dict[str, Any]]]
            Data to be plotted.
        nb_frames: int
            Number of frames to use in the animation. If None, the second dimension of
            the provided data arrays is used.
        title : Optional[str], optional
            Title to give to the plot. The default is None.
        xlabel : Optional[str], optional
            Label for the xaxis. The default is None.
        ylabel : Optional[str], optional
            Label for the yaxis. The default is None.

        Raises
        ------
        ValueError
            If the provided `data` dictionary contains inconsistent arrays.

        Returns
        -------
        None

        """
        ax: Axes = self.ax_dict[ax_name]

        # store all data in a list
        x_list: List[NDArrayFloat] = []
        y_list: List[NDArrayFloat] = []
        # The results are stored in plot_dict and allow updating the values.
        plot_dict = {}

        for label, val in data.items():
            kwargs: Dict[str, Any] = val.get("kwargs", {})
            x = val.get("x", None)
            _val = val.get("y")
            if _val is not None:
                y: NDArrayFloat = _val
            else:
                raise ValueError(
                    f'Error with data arguments: for key "{label}" y must be given!'
                )

            # Generate a series to adjust the y axis bounds without setting
            # y_extend = np.nanmax(y_list) - np.nanmin(y_list)
            y_extend = np.linspace(np.nanmin(y), np.nanmax(y), y.shape[0])

            if x is not None:
                x_extend = np.linspace(np.nanmin(x), np.nanmax(x), x.shape[0])
                x_list.append(x.reshape(x.shape[0], -1))  # make sure that x is 2d
            else:
                x_extend = np.arange(y.shape[0])
            plot_dict[label] = ax.plot(x_extend, y_extend, label=label, **kwargs)[0]
            y_list.append(y)

        nb_steps: int = y_list[0].shape[1]

        # Number of x and y consistency
        if len(x_list) != 0 and (len(x_list) != len(y_list)):
            raise ValueError(
                "When the x vector is provided, it must be for each y vector!"
            )

        # Check that all arrays have the same number of frames
        if not all((y_list[0].shape[1] == y.shape[1] for y in y_list[1:])):
            raise ValueError(
                "Not all given y arrays have the same number of steps (last dimension)!"
            )
        if len(x_list) > 1:
            if not all((x_list[0].shape[1] == x.shape[1] for x in x_list[1:])):
                raise ValueError(
                    "Not all given x arrays have the same number "
                    "of steps (last dimension)!"
                )

        # Check the dimensions
        if not all((y_list[0].shape[0] == y.shape[0] for y in y_list[1:])):
            raise ValueError(
                "Not all given y arrays have the same first dimension (n values)!"
            )

        if title:
            ax.set_title(title, fontweight="bold")
        if xlabel:
            ax.set_xlabel(xlabel, fontweight="bold")
        if ylabel:
            ax.set_ylabel(ylabel, fontweight="bold")

        def _init() -> List[Line2D]:
            """Only required for blitting to give a clean slate."""
            for label in data.keys():
                plot_dict[label].set_ydata(
                    np.full(y_list[0][:, 0].size, fill_value=np.nan),
                )
            return list(plot_dict.values())

        _nb_frames: int = _get_nb_frames(nb_frames, nb_steps)

        def _animate(frame_index: int) -> List[Line2D]:
            """Update the data of the plot."""
            # subtract -1 to nb_steps and _nb_frames so that when
            # frame_index = 0, we get the first element of x_list, and when
            # frame_index = _nb_frames - 1, we get the last element of x_list.
            data_index: int = int((nb_steps - 1) / (_nb_frames - 1) * frame_index)
            for index, label in enumerate(data.keys()):
                # update x
                if len(x_list) != 0:
                    try:
                        plot_dict[label].set_xdata(x_list[index][:, data_index])
                    except IndexError:
                        pass
                # update y
                plot_dict[label].set_ydata(
                    y_list[index][:, data_index],
                )
            return list(plot_dict.values())

        self.init_animations_list.append(_init)
        self.animations_list.append(_animate)

    def animated_multi_imshow(
        self,
        ax_names: Iterable[str],
        data: Dict[str, NDArrayFloat],
        fig: Optional[Union[Figure, SubFigure]] = None,
        nb_frames: Optional[int] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        imshow_kwargs: Optional[Dict[str, Any]] = None,
        cbar_kwargs: Optional[Dict[str, Any]] = None,
        is_symmetric_cbar: bool = False,
        cbar_title: Optional[str] = None,
    ) -> Colorbar:
        """
        Plot an animated 2D field with imshow.

        The number of frames can be determined automatically from the data.

        Parameters
        ----------
        ax_names : str
            List of axis names in which to plot the data. The order of axes must be
            the same as that of the data.
        data : Dict[str, Union[np.ndarray, Dict[str, Any]]]
            Data to be plotted.
        fig: Optional[Figure, SubFigure]
            Which figure to consider for the color bar. By default, use self.fig.
        nb_frames : Optional[int]
            Number of frame to use. By default, it is the number of provided steps,
            that is to say the last dimension of the arrays. If the number of frames
            exceeds the number of steps available, some steps will be repeated once
            or more and a warning is raised.
        xlabel : Optional[str], optional
            Label to apply to all xaxes. The default is None.
        ylabel : Optional[str], optional
            Label to apply to all yaxes. The default is None.
        imshow_kwargs: Optional[Dict[str, Any]] optional
            Optional arguments for `plt.imshow`. The default is None.

        Examples
        --------
        Examples can be given using either the ``Example`` or ``Examples``
        sections. Sections support any reStructuredText formatting, including
        literal blocks::

            $ python example_numpy.py

        Raises
        ------
        ValueError
            If the provided `data` dictionary contains inconsistent arrays.

        Returns
        -------
        None

        """
        axes: list[Axes] = [self.ax_dict[ax_name] for ax_name in ax_names]
        # The number of ax_name and data provided should be the same:
        _check_axes_and_data_consistency(axes, data)

        # Add some default values for imshow and colorbar
        _imshow_kwargs: Dict[str, Any] = _apply_default_imshow_kwargs(imshow_kwargs)
        _cbar_kwargs: Dict[str, Any] = _apply_default_colorbar_kwargs(cbar_kwargs, axes)

        # store all data in a list
        data_list = []
        # The results are stored in plot_dict and allow updating the values.

        images_dict: Dict[str, AxesImage] = {}
        for j, (label, values) in enumerate(data.items()):
            ax = self.ax_dict[ax_names[j]]
            if not len(values.shape) == 3:
                raise ValueError(
                    f'The given data for "{label}" has shape {values.shape} '
                    "whereas it should be three dimensional!"
                )

            # Need to transpose because the dimensions (M, N) define the rows and
            # columns
            # Also, need to copy the _imshow_kwargs to avoid its update. Otherwise the
            # colorbar scaling does not work properly
            images_dict[label] = ax.imshow(
                values[:, :, 0].T, **copy.deepcopy(_imshow_kwargs)
            )
            data_list.append(values)

            ax.label_outer()
            ax.set_title(label, weight="bold")
            if xlabel is not None:
                ax.set_xlabel(xlabel, fontweight="bold")
            if ylabel is not None:
                ax.set_ylabel(ylabel, fontweight="bold")

        nb_steps: int = data_list[0].shape[2]

        # Check that all arrays have the same number of timesteps
        if not all((nb_steps == x.shape[2] for x in data_list[1:])):
            raise ValueError(
                "Not all given arrays have the same number of steps (last dimension)!"
            )

        # norm both data and colobar
        _norm_data_and_cbar(
            list(images_dict.values()),
            list(data.values()),
            _imshow_kwargs,
            is_symmetric_cbar,
        )

        if fig is None:
            _fig: Union[Figure, SubFigure] = self.fig
        else:
            _fig: Union[Figure, SubFigure] = fig

        # pylint: disable=C0123 # use isinstance instead
        cbar: Colorbar = _fig.colorbar(list(images_dict.values())[0], **_cbar_kwargs)
        if cbar_title is not None:
            cbar.ax.get_yaxis().labelpad = 20
            cbar.ax.set_ylabel(cbar_title, rotation=270)

        def _init() -> List[AxesImage]:
            """Only required for blitting to give a clean slate."""
            for label, values in data.items():
                images_dict[label].set_data(
                    np.full(values[:, :, 0].T.shape, fill_value=np.nan),
                )
            return list(images_dict.values())

        _nb_frames: int = _get_nb_frames(nb_frames, nb_steps)

        def _animate(frame_index: int) -> List[AxesImage]:
            """Update the data of the plot."""
            # subtract -1 to nb_steps and _nb_frames so that when
            # frame_index = 0, we get the first element of x_list, and when
            # frame_index = _nb_frames - 1, we get the last element of x_list.
            data_index: int = int((nb_steps - 1) / (_nb_frames - 1) * frame_index)
            for label in data.keys():
                images_dict[label].set_data(
                    data[label][:, :, data_index].T,
                )
            return list(images_dict.values())

        self.init_animations_list.append(_init)
        self.animations_list.append(_animate)

        return cbar
