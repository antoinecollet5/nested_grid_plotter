"""
Provide plotter classes.

These classes allows to wrap the creation of figures with matplotlib and to use
a unified framework.
"""

from __future__ import annotations

import abc
import copy
from collections import ChainMap
from itertools import product
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.figure import Figure, SubFigure
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox
from numpy.typing import ArrayLike
from typing_extensions import Literal

from nested_grid_plotter.utils import (
    add_grid_and_tick_prams_to_axis,
    object_or_object_sequence_to_list,
)

# pylint: disable=C0103 # does not confrom to snake case naming style


class NestedBuilder(abc.ABC):
    """Abstract class for nested builders."""

    @abc.abstractmethod
    def __call__(
        self,
        fig: Union[Figure, SubFigure],
        figname: str,
        grouped_sf_dict: Dict[str, Dict[str, SubFigure]],
        grouped_ax_dict: Dict[str, Dict[str, Axes]],
    ) -> None: ...


class SubplotMosaicBuilder(NestedBuilder):
    """Args and kwargs for Figure.subfigures routine."""

    def __init__(
        self,
        mosaic,
        *,
        sharex: bool = False,
        sharey: bool = False,
        width_ratios: Optional[ArrayLike] = None,
        height_ratios: Optional[ArrayLike] = None,
        empty_sentinel: Any = ".",
        subplot_kw: Optional[Dict[str, Any]] = None,
        per_subplot_kw: Optional[Dict[str, Any]] = None,
        gridspec_kw: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Build a layout of Axes based on ASCII art or nested lists.

        This is a helper function to build complex GridSpec layouts visually.

        See :ref:`mosaic`
        for an example and full API documentation

        Parameters
        ----------
        mosaic : list of list of {hashable or nested} or str

            A visual layout of how you want your Axes to be arranged
            labeled as strings.  For example ::

                x = [["A panel", "A panel", "edge"], ["C panel", ".", "edge"]]

            produces 4 Axes:

            - 'A panel' which is 1 row high and spans the first two columns
            - 'edge' which is 2 rows high and is on the right edge
            - 'C panel' which in 1 row and 1 column wide in the bottom left
            - a blank space 1 row and 1 column wide in the bottom center

            Any of the entries in the layout can be a list of lists
            of the same form to create nested layouts.

            If input is a str, then it can either be a multi-line string of
            the form ::

                            '''
                            AAE
                            C.E
                            '''

            where each character is a column and each line is a row. Or it
            can be a single-line string where rows are separated by ``;``::

                            "AB;CC"

            The string notation allows only single character Axes labels and
            does not support nesting but is very terse.

            The Axes identifiers may be `str` or a non-iterable hashable
            object (e.g. `tuple` s may not be used).

        sharex, sharey : bool, default: False
            If True, the x-axis (*sharex*) or y-axis (*sharey*) will be shared
            among all subplots.  In that case, tick label visibility and axis
            units behave as for `subplots`.  If False, each subplot's x- or
            y-axis will be independent.

        width_ratios : array-like of length *ncols*, optional
            Defines the relative widths of the columns. Each column gets a
            relative width of ``width_ratios[i] / sum(width_ratios)``.
            If not given, all columns will have the same width.  Equivalent
            to ``gridspec_kw={'width_ratios': [...]}``. In the case of nested
            layouts, this argument applies only to the outer layout.

        height_ratios : array-like of length *nrows*, optional
            Defines the relative heights of the rows. Each row gets a
            relative height of ``height_ratios[i] / sum(height_ratios)``.
            If not given, all rows will have the same height. Equivalent
            to ``gridspec_kw={'height_ratios': [...]}``. In the case of nested
            layouts, this argument applies only to the outer layout.

        subplot_kw : dict, optional
            Dictionary with keywords passed to the `.Figure.add_subplot` call
            used to create each subplot.  These values may be overridden by
            values in *per_subplot_kw*.

        per_subplot_kw : dict, optional
            A dictionary mapping the Axes identifiers or tuples of identifiers
            to a dictionary of keyword arguments to be passed to the
            `.Figure.add_subplot` call used to create each subplot.  The values
            in these dictionaries have precedence over the values in
            *subplot_kw*.

            If *mosaic* is a string, and thus all keys are single characters,
            it is possible to use a single string instead of a tuple as keys;
            i.e. ``"AB"`` is equivalent to ``("A", "B")``.

            .. versionadded:: 3.7

        gridspec_kw : dict, optional
            Dictionary with keywords passed to the `.GridSpec` constructor used
            to create the grid the subplots are placed on. In the case of
            nested layouts, this argument applies only to the outer layout.
            For more complex layouts, users should use `.Figure.subfigures`
            to create the nesting.

        empty_sentinel : object, optional
            Entry in the layout to mean "leave this space empty".  Defaults
            to ``'.'``. Note, if *layout* is a string, it is processed via
            `inspect.cleandoc` to remove leading white space, which may
            interfere with using white-space as the empty sentinel.
        """

        self.mosaic = mosaic
        self.sharex: bool = sharex
        self.sharey: bool = sharey
        self.width_ratios = width_ratios
        self.height_ratios = height_ratios
        self.empty_sentinel = empty_sentinel
        self.subplot_kw = subplot_kw
        self.per_subplot_kw = per_subplot_kw
        self.gridspec_kw = gridspec_kw

    def __call__(
        self,
        fig: Union[Figure, SubFigure],
        figname: str,
        grouped_sf_dict: Dict[str, Dict[str, SubFigure]],
        grouped_ax_dict: Dict[str, Dict[str, Axes]],
    ) -> None:
        grouped_ax_dict[figname] = fig.subplot_mosaic(**self.__dict__)


class SubfigsBuilder(NestedBuilder):
    """Args and kwargs for Figure.subfigures routine."""

    def __init__(
        self,
        *,
        nrows: int = 1,
        ncols: int = 1,
        squeeze: bool = True,
        wspace: Optional[float] = None,
        hspace: Optional[float] = None,
        width_ratios: Optional[ArrayLike] = None,
        height_ratios: Optional[ArrayLike] = None,
        sub_builders: Optional[Dict[str, NestedBuilder]] = None,
        **kwargs,
    ) -> None:
        """
        Initiate the instance.

        Parameters
        ----------
        nrows, ncols : int, default: 1
            Number of rows/columns of the subfigure grid.

        squeeze : bool, default: True
            If True, extra dimensions are squeezed out from the returned
            array of subfigures.

        wspace, hspace : float, default: None
            The amount of width/height reserved for space between subfigures,
            expressed as a fraction of the average subfigure width/height.
            If not given, the values will be inferred from rcParams if using
            constrained layout (see `~.ConstrainedLayoutEngine`), or zero if
            not using a layout engine.

        width_ratios : array-like of length *ncols*, optional
            Defines the relative widths of the columns. Each column gets a
            relative width of ``width_ratios[i] / sum(width_ratios)``.
            If not given, all columns will have the same width.

        height_ratios : array-like of length *nrows*, optional
            Defines the relative heights of the rows. Each row gets a
            relative height of ``height_ratios[i] / sum(height_ratios)``.
            If not given, all rows will have the same height.
        """
        self.nrows: int = nrows
        self.ncols: int = ncols
        self.sub_builders = sub_builders
        self.squeeze: bool = squeeze
        self.wspace = wspace
        self.hspace = hspace
        self.width_ratios = width_ratios
        self.height_ratios = height_ratios
        self.kwargs: Dict[str, Any] = kwargs

    def __call__(
        self,
        fig: Union[Figure, SubFigure],
        figname: str,
        grouped_sf_dict: Dict[str, Dict[str, SubFigure]],
        grouped_ax_dict: Dict[str, Dict[str, Axes]],
    ) -> None:
        # treat exception first
        if self.sub_builders is not None:
            if len(self.sub_builders) != self.nrows * self.ncols:
                raise Exception(
                    f"Error while creating subfigures for {figname}, "
                    f"{len(self.sub_builders)} builders have been "
                    f"provided, but there are {self.nrows} rows and {self.ncols} cols, "
                    f"i.e., {self.nrows * self.ncols} builders expected!"
                )

        # Note subfigure(...) returns a SubFigure instance or a numpy array of
        # subfigure with shape (nrows, ncols)
        # Here with ensure a flat sequence
        new_subfigs: Sequence[SubFigure] = np.asarray(
            object_or_object_sequence_to_list(
                fig.subfigures(
                    nrows=self.nrows,
                    ncols=self.ncols,
                    squeeze=self.squeeze,  # type: ignore
                    wspace=self.wspace,
                    hspace=self.hspace,
                    width_ratios=self.width_ratios,
                    height_ratios=self.height_ratios,
                    **self.kwargs,
                )
            )
        ).flatten()

        grouped_sf_dict[figname] = {}

        if self.sub_builders is not None:
            for new_subfig, (sf_name, builder) in zip(
                new_subfigs, self.sub_builders.items()
            ):
                grouped_sf_dict[figname][sf_name] = new_subfig
                builder(new_subfig, sf_name, grouped_sf_dict, grouped_ax_dict)
        else:
            # Here we need to treat the case with and without
            for n, (i, j) in enumerate(product(range(self.nrows), range(self.ncols))):
                sf_name = f"{figname if figname != 'fig' else 'subfig'}_{n + 1}"
                grouped_sf_dict[figname][sf_name] = new_subfigs[n]
                grouped_ax_dict[sf_name] = {
                    f"{sf_name}_ax1-1": new_subfigs[n].add_subplot()
                }


class NestedGridPlotter:
    """
    General class to wrap matplotlib plots.

    The paticularity is that each axis is given a unique name and each subfigure is
    given a unique name too.
    """

    def __init__(
        self,
        fig: Optional[Figure] = None,
        builder: Optional[NestedBuilder] = None,
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
                                        mosaic=[
                                            ["ax11", "ax12", "ax13", "ax14"],
                                            ["ax21", "ax22", "ax23", "ax24"],
                                            ["ax31", "ax32", "ax33", "ax34"],
                                        ],
                                        sharey=True,
                                        sharex=True,
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
        .. code-block:: python
                          import nested_grid_plotter as ngp

                          plotter = ngp.NestedGridPlotter(
                              ngp.Figure(constrained_layout=True, figsize=(18, 14)),
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
        if fig is None:
            self.fig: Figure = Figure()
        else:
            self.fig = fig

        # initiate subfigures and axes references
        self.grouped_ax_dict: Dict[str, Dict[str, Axes]] = {}
        self.grouped_sf_dict: Dict[str, Dict[str, SubFigure]] = {}

        # build subfigures and mosaic
        if builder is None:
            builder = SubplotMosaicBuilder([["ax1-1"]])
        builder(self.fig, "fig", self.grouped_sf_dict, self.grouped_ax_dict)

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
        """Return a flatten version of `grouped_ax_dict`."""
        # we cannot use reversed because of dicts are not reversible in py3.7
        # so we convert to list and reverse instead
        return dict(ChainMap(*list(self.grouped_ax_dict.values())[::-1]))

    @property
    def sf_dict(self) -> Dict[str, SubFigure]:
        """Return a flatten version of `grouped_sf_dict`."""
        # we cannot use reversed because of dicts are not reversible in py3.7
        # so we convert to list and reverse instead
        return dict(ChainMap(*list(self.grouped_sf_dict.values())[::-1]))

    @property
    def axes(self) -> List[Axes]:
        """Return all axes as a list."""
        return list(self.ax_dict.values())

    def close(self) -> None:
        """Close the current figure."""
        plt.close(self.fig)

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
        temp: Dict[str, List[str]] = {}
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
        bbox_extra_artists = [
            *kwargs.get("bbox_extra_artists", ()),
            *self.fig.legends,
            *[lgd for fig in self.sf_dict.values() for lgd in fig.legends],
        ]
        for fig in [self.fig, *self.sf_dict.values()]:
            if fig._supxlabel is not None:  # type: ignore
                bbox_extra_artists.append(fig._supxlabel)  # type: ignore
            if fig._supylabel is not None:  # type: ignore
                bbox_extra_artists.append(fig._supylabel)  # type: ignore
            if fig._suptitle is not None:  # type: ignore
                bbox_extra_artists.append(fig._suptitle)  # type: ignore
        kwargs.update({"bbox_extra_artists": tuple(bbox_extra_artists)})
        self.fig.savefig(*args, **kwargs, bbox_inches=bbox_inches)
        # need this if 'transparent=True' to reset colors
        self.fig.canvas.draw_idle()

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
        if subfig_name not in self.sf_dict.keys():
            raise ValueError(f'The subfigure "{subfig_name}" does not exists!')
        return self.sf_dict[subfig_name]

    def _iterate_subfig_grouped_axes(
        self, subfig_name: str
    ) -> Iterator[Dict[str, Axes]]:
        if subfig_name in self.grouped_ax_dict.keys():
            yield self.grouped_ax_dict[subfig_name]
            return
        for sf_name in self.grouped_sf_dict[subfig_name].keys():
            for tmp in self._iterate_subfig_grouped_axes(sf_name):
                yield tmp

    def get_subfigure_ax_dict(self, subfig_name: str) -> Dict[str, Axes]:
        return {
            k: v
            for _dict in self._iterate_subfig_grouped_axes(subfig_name)
            for k, v in _dict.items()
        }

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
        ax: Axes = self.ax_dict[ax_name]
        handles, labels = ax.get_legend_handles_labels()

        # Handle twin axes
        if ax.figure is not None:
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
        self, fig_name: Optional[str] = None, remove_duplicates: bool = True
    ) -> Tuple[List[Artist], List[str]]:
        """
        Gather the legend items from all axes of the figure or of one subfigure.

        Parameters
        ----------
        fig_name : Optional[str], optional
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
        if fig_name is None:
            source = self.ax_dict
        else:
            source = self.get_subfigure_ax_dict(fig_name)

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
    ) -> Optional[Legend]:
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
        Optional[Legend]
            The created legend instance. None if no handles nor labels have been found.
        """
        handles, labels = self._gather_figure_legend_items(name)
        if len(handles) == 0:
            return None

        # Get the correct object
        if name is None:
            obj: Union[Figure, SubFigure] = self.fig
            bbox_transform = obj.transFigure
        else:
            obj = self.sf_dict[name]
            bbox_transform = obj.transSubfigure
        # Make sure that the figure of the handles is the figure of the legend
        # RunTimeError Can not put single artist in more than one figure
        for i in range(len(handles)):
            if handles[i].figure is not obj:
                handles[i] = copy.copy(handles[i])
                handles[i].figure = obj

        # Remove a potentially existing legend
        obj.legends.clear()

        bbox_to_anchor: List[float] = get_bbox_to_anchor(loc)
        bbox_to_anchor[0] += bbox_x_shift
        bbox_to_anchor[1] += bbox_y_shift

        return obj.legend(
            handles,
            labels,
            loc="center",
            bbox_to_anchor=bbox_to_anchor,
            bbox_transform=bbox_transform,
            **kwargs,
        )

    def add_axis_legend_outside_frame(
        self,
        ax_name: str,
        bbox_x_shift: Optional[float] = None,
        bbox_y_shift: Optional[float] = None,
        loc: Literal["left", "right", "top", "bottom"] = "bottom",
        borderaxespad: float = 1.0,
        **kwargs: Any,
    ) -> Optional[Legend]:
        """
        Add a legend to the ax outside the ax frame.

        Parameters
        ----------
        ax_name : str
            The name of the ax for which to add a legend outside the frame.
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
        Optional[Legend]
            The created legend instance. None if no handles nor labels have been found.
        """
        handles, labels = self._remove_dulicated_legend_items(
            *self._get_axis_legend_items(ax_name)
        )

        # No handles = no need for a legend
        if len(handles) == 0:
            return None

        ax = self.ax_dict[ax_name]

        # get default values
        bbox_to_anchor: List[float] = get_bbox_to_anchor(loc)

        # user adjustment
        if bbox_x_shift is not None:
            bbox_to_anchor[0] += bbox_x_shift
        if bbox_y_shift is not None:
            bbox_to_anchor[1] += bbox_y_shift

        # Generate the figure a first time
        lgd = ax.legend(
            handles,
            labels,
            loc="center",
            bbox_to_anchor=bbox_to_anchor,
            bbox_transform=ax.transAxes,
            borderaxespad=borderaxespad,
            **kwargs,
        )

        # Handle cases with non automatic adjustment of the legend vertical/horizontal
        # position.
        if loc in ["bottom", "top"]:
            if bbox_x_shift is not None:
                return lgd
        else:
            if bbox_x_shift is not None:
                return lgd

        # The following deals with automatic position adjustment

        # First we update the figure with the layout engine, ex: ConstrainedLayout
        engine = self.fig.get_layout_engine()
        if engine is not None:
            engine.execute(self.fig)
        else:
            return lgd

        # We estimate the bbox_to_anchor adjustment from tight_boxes
        # This is not exact and depends on tight or constrained layout

        tot_bbox: Bbox = ax.get_tightbbox()  # type: ignore
        ax_bbox: Bbox = ax.get_tightbbox(
            bbox_extra_artists=[
                elt
                for elt in ax.get_default_bbox_extra_artists()
                if not isinstance(elt, Legend)
            ]
        )  # type: ignore
        frame_bbox = get_frame_bbox(ax)
        lgd_bbox: Bbox = lgd.get_tightbbox()  # type: ignore

        # take the legend border axespad into account.
        pad: float = lgd.borderaxespad * lgd.prop.get_size()

        if loc in ["left", "right"]:
            # total x extent for the axis
            dx_tot = tot_bbox.xmax - tot_bbox.xmin
            # x extent of the frame + ylabels + yticks etc. Not legend.
            dx_ax = ax_bbox.xmax - ax_bbox.xmin
            # x extent of ylabels + yticks etc.
            dx_ax_no_frame = dx_ax - (frame_bbox.xmax - frame_bbox.xmin)
            # x extent of the created legend
            dx_lgd = lgd_bbox.xmax - lgd_bbox.xmin

            # we must consider the transform (tight or constrained)
            if engine is not None:
                den: float = dx_tot - dx_lgd - dx_ax_no_frame
            else:
                den = dx_ax - dx_ax_no_frame

            if loc in ["left"]:
                bbox_to_anchor[0] -= (
                    dx_lgd / 2 + frame_bbox.xmin - ax_bbox.xmin + pad
                ) / den
            else:
                bbox_to_anchor[0] += (
                    dx_lgd / 2 + ax_bbox.xmax - frame_bbox.xmax + pad
                ) / den

        else:
            # total y extent for the axis
            dy_tot = tot_bbox.ymax - tot_bbox.ymin
            # y extent of the frame + xlabels + xticks etc. Not legend.
            dy_ax = ax_bbox.ymax - ax_bbox.ymin
            # y extent of xlabels + xticks etc.
            dy_ax_no_frame = dy_ax - (frame_bbox.ymax - frame_bbox.ymin)
            # y extent of the created legend
            dy_lgd = lgd_bbox.ymax - lgd_bbox.ymin

            # we must consider the transform (tight or constrained)
            if engine is not None:
                den = dy_tot - dy_lgd - dy_ax_no_frame
            else:
                den = dy_ax

            if loc in ["bottom"]:
                bbox_to_anchor[1] -= (
                    dy_lgd / 2 + frame_bbox.ymin - ax_bbox.ymin + pad
                ) / den
            else:
                bbox_to_anchor[1] += (
                    dy_lgd / 2 + ax_bbox.ymax - frame_bbox.ymax + pad
                ) / den

        # while is_lgd_overlapping_axis(ax, lgd):
        #     if loc in ["bottom"]:
        #         bbox_to_anchor[1] -= 0.025

        lgd = ax.legend(
            handles,
            labels,
            loc="center",
            bbox_to_anchor=bbox_to_anchor,
            bbox_transform=ax.transAxes,
            borderaxespad=borderaxespad,
            **kwargs,
        )

        # if lyte is not None:
        #     lyte.execute(self.fig)

        return lgd

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
        for subfig in self.sf_dict.values():
            subfig.legends.clear()


def get_bbox_to_anchor(loc: str) -> List[float]:
    try:
        return {
            "left": [0.0, 0.5],
            "right": [1.0, 0.5],
            "top": [0.5, 1.0],
            "bottom": [0.5, 0.0],
        }[loc]
    except KeyError as e:
        raise ValueError(
            'authorized values for loc are "left", "right", "top", "bottom"!'
        ) from e


def get_frame_bbox(ax: Axes) -> Bbox:
    return Bbox(
        [
            [
                ax.spines.right.get_window_extent().xmax,
                ax.spines.top.get_window_extent().ymax,
            ],
            [
                ax.spines.left.get_window_extent().xmin,
                ax.spines.bottom.get_window_extent().ymin,
            ],
        ]
    )


def is_lgd_overlapping_axis(ax: Axes, lgd: Legend) -> bool:
    ax_bbox = ax.get_tightbbox(
        bbox_extra_artists=[
            elt
            for elt in ax.get_default_bbox_extra_artists()
            if not isinstance(elt, Legend)
        ]
    )
    lgd_bbox = lgd.get_tightbbox()

    # take the legend border axespad into account.
    pad = lgd.borderaxespad * lgd.prop.get_size()

    return (
        ax_bbox.xmax >= lgd_bbox.xmin - pad and lgd_bbox.xmax + pad >= ax_bbox.xmin
    ) and (ax_bbox.ymax >= lgd_bbox.ymin - pad and lgd_bbox.ymax + pad >= ax_bbox.ymin)
