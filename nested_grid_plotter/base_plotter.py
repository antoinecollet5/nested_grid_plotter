"""
Provide plotter classes.

These classes allows to wrap the creation of figures with matplotlib and to use
a unified framework.
"""

import copy
from collections import ChainMap
from itertools import product
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from typing_extensions import Literal

from nested_grid_plotter.utils import add_grid_and_tick_prams_to_axis

# pylint: disable=C0103 # does not confrom to snake case naming style


class NestedGridPlotter:
    """General class to wrap matplotlib plots."""

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
        fig_params: Dict[str, Any]
            Parameters for :class:`matplotlib.figure.Figure`.
        subfigs_params: Dict[str, Any]
            Parameters for :meth:`matplotlib.figure.Figure.subfigures`.
        subplots_mosaic_params: Dict[str, Dict[str, Any]]
            Parameters for the subplots in the subfigures.
            (See :func:`matplotlib.pyplot.subplot_mosaic`).

            .. code-block:: python
              :linenos:
              :caption: Example

                  subplots_mosaic_params = {
                    "unique": dict(
                        mosaic = [
                            ["ax11", "ax12", "ax13", "ax14"],
                            ["ax21", "ax22", "ax23", "ax24"],
                            ["ax31", "ax32", "ax33", "ax34"]
                        ],
                        sharey = True,
                        sharex = True
                        )
                    }

        Attributes
        ----------
        fig: :class:`matplotlib.figure.Figure`
            Description.
        subfigs: Dict[str, :class:`matplotlib.figure.SubFigure`]
            Description.
        ax_dict: Dict[str, Dict[str, Axes]]
            Nested dict, first level with subfigures names and second with
            axes names.

        Example
        -------

        subplots_mosaic_params = {
            "unique": dict(
                mosaic = [
                    ["ax11", "ax12", "ax13", "ax14"],
                    ["ax21", "ax22", "ax23", "ax24"],
                    ["ax31", "ax32", "ax33", "ax34"]
                ],
                sharey = True,
                sharex = True
                )
            }

        plotter = NestedGridPlotter(
            fig_params={"constrained_layout": True, "figsize": (18, 14)},
            subplots_mosaic_params={
                "fig0": dict(
                    mosaic=[
                        ["ax1-1", "ax1-2"],
                        ["ax2-1", "ax2-2"],
                        ["ax3-1", "ax3-2"],
                        ["ax4-1", "ax4-2"],
                    ],
                    sharey=False,
                    sharex=True,
                )
            },
        )
        """
        fig_params = {} if fig_params is None else fig_params
        subfigs_params = {} if subfigs_params is None else subfigs_params
        subplots_mosaic_params = (
            {} if subplots_mosaic_params is None else subplots_mosaic_params
        )

        self.fig: Figure = plt.figure(**fig_params)
        _subfigs = self.fig.subfigures(**subfigs_params)

        self.subfigs: Dict[str, SubFigure] = {}
        self.grouped_ax_dict: Dict[str, Any] = {}

        nrows: int = subfigs_params.pop("nrows", 1)
        ncols: int = subfigs_params.pop("ncols", 1)

        if len(subplots_mosaic_params) == 0:
            self._add_default_subplots_to_subfigures(_subfigs, nrows, ncols)
        else:
            self._check_consistency_between_subfigures_and_subplots_params(
                subplots_mosaic_params, nrows, ncols
            )
            self._create_subplots_from_user_params(_subfigs, subplots_mosaic_params)
        self._check_if_subplot_names_are_unique()

        # Two dict to store the handles and labels to add to the legend
        # The key is the number of the id of the axis matching the handles
        self._additional_handles: Dict[str, Any] = {
            ax_name: [] for ax_name in self.ax_dict.keys()
        }
        self._additional_labels: Dict[str, Any] = {
            ax_name: [] for ax_name in self.ax_dict.keys()
        }

    @property
    def ax_dict(self) -> Dict[str, Axes]:
        """Return a flatten version of `ax_dict`."""
        # we cannot use reversed because of dicts are not reversible in py3.7
        # so we convert to list and reverse instead
        return dict(ChainMap(*list(self.grouped_ax_dict.values())[::-1]))

    @property
    def axes(self) -> List[Axes]:
        """Return all axes as a list."""
        return list(self.ax_dict.values())

    def close(self) -> None:
        """Close the current figure."""
        plt.close(self.fig)

    def _add_default_subplots_to_subfigures(
        self,
        subfigs: Union[SubFigure, np.ndarray],
        nrows: int,
        ncols: int,
    ) -> None:
        """
        Add one subplot per subfigure and name it by default.

        It also gives a default name to the subfigures based on row and column
        indice.

        Parameters
        ----------
        subfigs : Union[Figure, np.ArrayLike[Figure]]
            Available subfigures. It is a :class:`matplotlib.figure.Figure` if there
            is only one row and one column, otherwise, a numpy array of
            :class:`matplotlib.figure.Figure`.
        nrows: int
            Number of rows for subfigures.
        ncols : int
            Number of columns for subfigures.

        Returns
        -------
        None
        """
        for n, (i, j) in enumerate(product(range(nrows), range(ncols))):
            try:
                self.subfigs[f"fig{i+1}-{j+1}"] = subfigs.flatten()[n]
            except (TypeError, AttributeError):
                self.subfigs[f"fig{i+1}-{j+1}"] = subfigs
            self.grouped_ax_dict[f"fig{i+1}-{j+1}"] = {
                f"ax{i+1}-{j+1}": self.subfigs[f"fig{i+1}-{j+1}"].add_subplot()
            }

    @staticmethod
    def _check_consistency_between_subfigures_and_subplots_params(
        subplots_mosaic_params: Dict[str, Dict[str, Any]],
        nrows: int,
        ncols: int,
    ) -> None:
        """
        Check the number consistency between subfigures and subplots.

        Parameters
        ----------
        subplots_mosaic_params : Dict[str, Dict[str, Any]]
            Parameters for the subplots in the subfigures.
            See subplot_mosaic.
        nrows: int
            Number of rows for subfigures.
        ncols : int
            Number of columns for subfigures.

        Raises
        ------
        Exception
            Raised if the number does not match..

        Returns
        -------
        None

        """
        if len(subplots_mosaic_params) > nrows * ncols:
            raise Exception(
                f"{len(subplots_mosaic_params)} subplot configurations have been "
                "provided for subplots_mosaic_params, but there are only "
                f"{nrows * ncols} subfigures!"
            )

    def _create_subplots_from_user_params(
        self,
        subfigs: Union[SubFigure, npt.NDArray[SubFigure]],
        subplots_mosaic_params: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Populate the subfigures with mosaic subplots using the user parameters.

        Both subfigures and axes are named from the parameters given.

        Parameters
        ----------
        subfigs : Union[Figure, np.ndarray]
            Available subfigures. It is a :class:`matplotlib.figure.Figure`
            if there is only one row and one column, otherwise, a numpy array
            of :class:`matplotlib.figure.Figure`.
        subplots_mosaic_params : Dict[str, Dict[str, Any]]
            DESCRIPTION.

        Returns
        -------
        None

        """
        # case with nrows == 1 & ncols == 1
        if isinstance(subfigs, SubFigure):
            _subfigs: List[SubFigure] = [
                subfigs
            ]  # make sure to have an iterable = unique subfigure
        # Case of a numpy array = multiple subfigures
        else:
            _subfigs: List[SubFigure] = list(subfigs.ravel())

        for i, (name, params) in enumerate(subplots_mosaic_params.items()):
            self.subfigs[name] = _subfigs[i]
            mosaic = params.pop("mosaic")
            self.grouped_ax_dict[name] = self.subfigs[name].subplot_mosaic(
                mosaic, **params
            )

    def _check_if_subplot_names_are_unique(self) -> None:
        """
        Check if a subplot name is not used in two different subfigures.

        This is necessary otherwise, one or more subplots would be missing
        from the `ax_dict`.

        Raises
        ------
        Exception
            Indicate which axis names are duplicated and on which subfigures .

        Returns
        -------
        None

        """
        temp = {}
        for k, v in self.grouped_ax_dict.items():
            for k2 in v.keys():
                temp.setdefault(k2, []).append(k)
        non_unique_keys = [k for k, v in temp.items() if len(v) > 1]
        if len(non_unique_keys) == 1:
            raise Exception(
                f"The name {non_unique_keys} has been used in "
                "more than one subfigures!"
            )
        if len(non_unique_keys) > 1:
            raise Exception(
                f"The names {non_unique_keys} have been used in "
                "more than one subfigures!"
            )

    def savefig(self, *args: Any, **kwargs: Any) -> None:
        """
        Save the current figure.

        Parameters
        ----------
        *args : Any
            Positional arguments for :meth:`matplotlib.figure.Figure.savefig`.
        **kwargs : Any
            Keywords arguments for :meth:`matplotlib.figure.Figure.savefig`.

        Returns
        -------
        None
        """
        # Ensure that all artists are saved (nothing should be cropped)
        # https://stackoverflow.com/questions/9651092/my-matplotlib-pyplot-legend-is-being-cut-off/42303455
        bbox_inches = kwargs.pop("bbox_inches", "tight")
        # make sure that if a fig legend as been added, it won't be cutoff by
        # the figure box
        kwargs.update(
            {
                "bbox_extra_artists": (
                    *kwargs.get("bbox_extra_artists", ()),
                    *self.fig.legends,
                    *[lgd for fig in self.subfigs.values() for lgd in fig.legends],
                )
            }
        )
        res = self.fig.savefig(*args, **kwargs, bbox_inches=bbox_inches)
        # need this if 'transparent=True' to reset colors
        self.fig.canvas.draw_idle()
        return res

    def identify_axes(self, fontsize: int = 48) -> None:
        """
        Draw the label in a large font in the center of the Axes.

        Parameters
        ----------
        ax_dict : Dict[str, Axes]
            Mapping between the title / label and the Axes.
        fontsize : int, optional
            How big the label should be.

        Returns
        -------
        None
        """
        for ax_name, ax in self.ax_dict.items():
            ax.text(
                0.5,
                0.5,
                ax_name,
                transform=ax.transAxes,
                ha="center",
                va="center",
                fontsize=fontsize,
                color="darkgrey",
            )

    def get_axis(self, ax_name: str) -> Axes:
        """
        Get an axis from the plotter.

        Parameters
        ----------
        ax_name : str
            Name of the axis to get.

        Returns
        -------
        Axes
            The desired axis.

        """
        if ax_name not in self.ax_dict.keys():
            raise ValueError(f'The axis "{ax_name}" does not exists!')
        return self.ax_dict[ax_name]

    def get_axes(self, ax_names: Sequence[str]) -> List[Axes]:
        """
        Get a sequence of axes from the plotter.

        Parameters
        ----------
        ax_names : Sequence[str]
            Name of the axes to get. Must be iterable.

        Returns
        -------
        Axes
            The desired axes.

        """
        return [self.get_axis(axn) for axn in ax_names]

    def get_subfigure(self, subfig_name: str) -> SubFigure:
        """
        Get an axis from the plotter.

        Parameters
        ----------
        subfig_name : str
            Name of the subfigure to get.

        Returns
        -------
        SubFigure
            The desired subfigure.

        """
        if subfig_name not in self.subfigs.keys():
            raise ValueError(f'The subfigure "{subfig_name}" does not exists!')
        return self.subfigs[subfig_name]

    def add_grid_and_tick_prams_to_all_axes(
        self, subfigure_name: Optional[str] = None, **kwargs: Any
    ) -> None:
        """
        Add a grid to all the axes of the figure.

        Parameters
        ----------
        subfigure_name : Optional[str], optional
            Name of the target subfigure. If None, apply to the all figure.
            The default is None.
        **kwargs : Any
            Keywords for `add_grid_and_thick_prams_to_axis`.

        Returns
        -------
        None

        """
        if subfigure_name is not None:
            for ax in self.grouped_ax_dict[subfigure_name].values():
                add_grid_and_tick_prams_to_axis(ax, **kwargs)
        else:
            for ax in self.ax_dict.values():
                add_grid_and_tick_prams_to_axis(ax, **kwargs)

    def _get_axis_legend_items(self, ax_name: str) -> Tuple[List[Artist], List[str]]:
        """
        Get the given axis legend handles and labels.

        Parameters
        ----------
        ax_name : str
            Name of the axis.

        Returns
        -------
        Tuple[List[Artist], List[str]]
            Handles and labels lists.

        """
        ax = self.ax_dict[ax_name]
        handles, labels = ax.get_legend_handles_labels()

        # Handle twin axes
        for other_ax in ax.figure.axes:
            if other_ax is ax:
                continue
            if other_ax.bbox.bounds == ax.bbox.bounds:
                _handles, _labels = other_ax.get_legend_handles_labels()
                handles += _handles
                labels += _labels

        # Add the additional handles and labels of the axis
        handles += self._additional_handles.get(ax_name, [])
        labels += self._additional_labels.get(ax_name, [])
        return handles, labels

    @staticmethod
    def _remove_dulicated_legend_items(
        handles: Sequence[Artist], labels: Sequence[str]
    ) -> Tuple[List[Artist], List[str]]:
        """Remove the duplicated legend handles and labels."""
        # remove the duplicates
        by_label = dict(zip(labels, handles))
        return list(by_label.values()), list(by_label.keys())

    def _gather_figure_legend_items(
        self, name: Optional[str] = None, remove_duplicates: bool = True
    ) -> Tuple[List[Artist], List[str]]:
        """
        Gather the legend items from all axes of the figure or of one subfigure.

        Parameters
        ----------
        name : Optional[str], optional
            The subfigure to which add the legend. If no name is given, it applies to
            the all figure. Otherwise to a specific subfigure. The default is None.
        remove_duplicates : bool, optional
            Whether to remove duplicated handle-label couples. The default is True.

        Returns
        -------
        Tuple[List[Artist], List[str]]
            Handles and labels lists.

        """
        handles, labels = [], []
        if name is None:
            source = self.ax_dict
        else:
            source = self.grouped_ax_dict[name]

        for ax_name in source.keys():
            hdl, lab = self._get_axis_legend_items(ax_name)
            handles += hdl
            labels += lab
        # remove the duplicates
        if remove_duplicates:
            handles, labels = self._remove_dulicated_legend_items(handles, labels)
        return handles, labels

    def add_fig_legend(
        self,
        name: Optional[str] = None,
        bbox_x_shift: float = 0.0,
        bbox_y_shift: float = 0.0,
        loc: Literal["left", "right", "top", "bottom"] = "bottom",
        **kwargs: Any,
    ) -> Tuple[List[Any], List[str]]:
        """
        Add a legend to the plot.

        To the main figure or to one subfigure.

        Parameters
        ----------
        name : Optional[str], optional
            The subfigure to which add the legend. If no name is given, it applies to
            the all figure. Otherwise to a specific subfigure. The default is None.
        bbox_x_shift : float, optional
            Legend vertical shift (up oriented). The default is 0.0.
        bbox_y_shift : float, optional
            Legend horizontal shift (right oriented). The default is 0.0.
        loc : Literal["left", "right", "top", "bottom"], optional
            Side on which to place the legend box. The default is "bottom".
        **kwargs : Any
            Additional arguments for `plt.legend`.

        Returns
        -------
        Tuple[List[Any], List[str]]
            Handles and labels lists.
        """
        handles, labels = self._gather_figure_legend_items(name)
        if len(handles) == 0:
            return [], []

        # Get the correct object
        if name is None:
            obj: Union[Figure, SubFigure] = self.fig
        else:
            obj: Union[Figure, SubFigure] = self.subfigs[name]

        # Make sure that the figure of the handles is the figure of the legend
        # RunTimeError Can not put single artist in more than one figure
        for i in range(len(handles)):
            if handles[i].figure is not obj:
                handles[i] = copy.copy(handles[i])
                handles[i].figure = obj

        # Remove a potentially existing legend
        obj.legends.clear()

        if loc == "left":
            bbox_to_anchor: list[float] = [-0.05, 0.5]
        elif loc == "right":
            bbox_to_anchor: list[float] = [1.05, 0.5]
        elif loc == "top":
            bbox_to_anchor: list[float] = [0.5, 1.05]
        elif loc == "bottom":
            bbox_to_anchor: list[float] = [0.5, -0.05]
        else:
            raise ValueError(
                'authorized values for loc are "left", "right", "top", "bottom"!'
            )

        bbox_to_anchor[0] += bbox_x_shift
        bbox_to_anchor[1] += bbox_y_shift

        obj.legend(
            handles,
            labels,
            loc="center",
            bbox_to_anchor=bbox_to_anchor,
            bbox_transform=obj.transFigure,
            **kwargs,
        )
        return handles, labels

    def add_axis_legend(
        self, ax_name: str, **kwargs: Any
    ) -> Tuple[List[Any], List[str]]:
        """
        Add a legend to the graphic.

        Parameters
        ----------
        ax_name : str
            Ax for which to add the legend.
        **kwargs : Any
            Additional arguments for `plt.legend`.

        Returns
        -------
        (Tuple[List[Any], List[str]])
            Tuple of list of handles and list of associated labels.

        """
        handles, labels = self._remove_dulicated_legend_items(
            *self._get_axis_legend_items(ax_name)
        )

        self.ax_dict[ax_name].legend(
            handles,
            labels,
            **kwargs,
        )
        return handles, labels

    def add_extra_legend_item(self, ax_name: str, handle: Any, label: str) -> None:
        """
        Add an extra legend item to the given axis.

        Parameters
        ----------
        ax_name : str
            Ax for which to add the item.
        handle : Any
            Handle to add to the legend.
        label : str
            Label associated to the given handle.

        Returns
        -------
        None

        """
        self._additional_handles[ax_name].append(handle)
        self._additional_labels[ax_name].append(label)

    def clear_all_axes(self) -> None:
        """
        Clear all the axes from their data and layouts.

        It also resets the additional handles and labels for the legend.
        """
        for ax in self.ax_dict.values():
            ax.clear()
        # Also clear the elements of the legend
        self._additional_handles = {}
        self._additional_labels = {}

        # Remove a potentially existing legends on fig and subfigs
        self.clear_fig_legends()

    def clear_fig_legends(self) -> None:
        """Remove all added figure legends"""
        # Remove a potentially existing legends on fig and subfigs
        self.fig.legends.clear()
        for subfig in self.subfigs.values():
            subfig.legends.clear()
