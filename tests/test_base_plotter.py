"""
Test the NestedGridPlotter base class.

Note that the tests are very similar to the examples found in the tutorial and
follow the same order. The

@author: Antoine COLLET
"""

from contextlib import contextmanager
from itertools import product

import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import SubFigure
from matplotlib.lines import Line2D

from nested_grid_plotter import NestedGridPlotter


@contextmanager
def does_not_raise():
    yield


@pytest.fixture
def tmp_folder(tmp_path_factory):
    """Create a temporary directory"""
    return tmp_path_factory.mktemp("tmp_folder")


def test_plotter_without_input_args():
    plotter = NestedGridPlotter()
    assert list(plotter.subfigs.keys()) == ["fig1-1"]
    assert list(plotter.grouped_ax_dict.keys()) == ["fig1-1"]
    assert list(plotter.grouped_ax_dict["fig1-1"].keys()) == ["ax1-1"]
    assert list(plotter.ax_dict.keys()) == ["ax1-1"]

    x = np.linspace(0, 2, 100)  # Sample data.
    ax = plotter.ax_dict["ax1-1"]
    ax.plot(x, x, label="linear")
    ax.plot(x, x**2, label="quadratic")
    ax.plot(x, x**3, label="cubic")
    ax.set_xlabel("x label")  # Add an x-label to the axes.
    ax.set_ylabel("y label")  # Add a y-label to the axes.
    ax.set_title("Simple Plot")  # Add a title to the axes.
    ax.legend()
    # Add a legend.
    # plt.show()


def test_multiple_subfigs_no_mosaic():
    plotter = NestedGridPlotter(
        fig_params={"constrained_layout": True},
        subfigs_params={"nrows": 2, "ncols": 3},
    )
    assert list(plotter.subfigs.keys()) == [
        "fig1-1",
        "fig1-2",
        "fig1-3",
        "fig2-1",
        "fig2-2",
        "fig2-3",
    ]
    assert list(plotter.grouped_ax_dict.keys()) == [
        "fig1-1",
        "fig1-2",
        "fig1-3",
        "fig2-1",
        "fig2-2",
        "fig2-3",
    ]
    for i, j in product([1, 2], [1, 2, 3]):
        assert list(plotter.grouped_ax_dict[f"fig{i}-{j}"].keys()) == [f"ax{i}-{j}"]
    assert sorted(list(plotter.ax_dict.keys())) == [
        "ax1-1",
        "ax1-2",
        "ax1-3",
        "ax2-1",
        "ax2-2",
        "ax2-3",
    ]
    plotter.identify_axes()  # Helper to add the name of the axis on the plot
    # plt.show()


def test_unique_subfig_with_mosaic():
    plotter = NestedGridPlotter(
        fig_params={
            "constrained_layout": True
        },  # Always use this to prevent overlappings
        subplots_mosaic_params={
            "my_subfigure_name": dict(
                mosaic=[["ax11", "ax12", "ax13"], ["ax21", "ax22", "ax23"]]
            ),
        },
    )
    assert list(plotter.subfigs.keys()) == ["my_subfigure_name"]
    assert list(plotter.grouped_ax_dict.keys()) == ["my_subfigure_name"]
    assert list(plotter.grouped_ax_dict["my_subfigure_name"].keys()) == [
        "ax11",
        "ax12",
        "ax13",
        "ax21",
        "ax22",
        "ax23",
    ]
    assert sorted(list(plotter.ax_dict.keys())) == [
        "ax11",
        "ax12",
        "ax13",
        "ax21",
        "ax22",
        "ax23",
    ]
    plotter.identify_axes()  # Helper to add the name of the axis on the plot
    # plt.show()


def test_multiple_subfigs_1_row_with_mosaic():
    plotter = NestedGridPlotter(
        fig_params={
            "constrained_layout": True,  # Always use this to prevent overlappings
            "figsize": (10, 10),
        },
        subfigs_params={"nrows": 1, "ncols": 2},
        subplots_mosaic_params={
            "the_left_sub_figure": dict(
                mosaic=[["lt1", "lt1"], ["lb1", "rb1"]],
                gridspec_kw=dict(height_ratios=[2, 1], width_ratios=[2, 1]),
                sharey=False,
            ),
            "the_right_sub_figure": dict(
                mosaic=[["l2", "rt2"], ["l2", "bt2"]],
                gridspec_kw=dict(height_ratios=[2, 1], width_ratios=[2, 1]),
                sharey=False,
            ),
        },
    )
    assert list(plotter.subfigs.keys()) == [
        "the_left_sub_figure",
        "the_right_sub_figure",
    ]
    assert list(plotter.grouped_ax_dict.keys()) == [
        "the_left_sub_figure",
        "the_right_sub_figure",
    ]
    assert list(plotter.grouped_ax_dict["the_left_sub_figure"].keys()) == [
        "lt1",
        "lb1",
        "rb1",
    ]
    assert list(plotter.grouped_ax_dict["the_right_sub_figure"].keys()) == [
        "l2",
        "rt2",
        "bt2",
    ]
    assert sorted(list(plotter.ax_dict.keys())) == [
        "bt2",
        "l2",
        "lb1",
        "lt1",
        "rb1",
        "rt2",
    ]
    plotter.identify_axes()  # Helper to add the name of the axis on the plot
    # plt.show()


def test_multiple_subfigs_2_rows_with_mosaic():
    plotter = NestedGridPlotter(
        fig_params={
            "constrained_layout": True,  # Always use this to prevent overlappings
            "figsize": (10, 10),
        },
        subfigs_params={"nrows": 2, "ncols": 2},
        subplots_mosaic_params={
            "the_top_left_sub_figure": dict(
                mosaic=[["ax1"], ["ax2"]],
                sharey=False,
            ),
            "the_top_right_sub_figure": dict(
                mosaic=[["ax3"], ["ax4"]],
                sharey=False,
            ),
            "the_bottom_left_sub_figure": dict(
                mosaic=[["ax5"], ["ax6"]],
                sharey=False,
            ),
            "the_bottom_right_sub_figure": dict(
                mosaic=[["ax7"], ["ax8"]],
                sharey=False,
            ),
        },
    )
    assert list(plotter.subfigs.keys()) == [
        "the_top_left_sub_figure",
        "the_top_right_sub_figure",
        "the_bottom_left_sub_figure",
        "the_bottom_right_sub_figure",
    ]
    assert list(plotter.grouped_ax_dict.keys()) == [
        "the_top_left_sub_figure",
        "the_top_right_sub_figure",
        "the_bottom_left_sub_figure",
        "the_bottom_right_sub_figure",
    ]
    assert list(plotter.grouped_ax_dict["the_top_left_sub_figure"].keys()) == [
        "ax1",
        "ax2",
    ]
    assert list(plotter.grouped_ax_dict["the_top_right_sub_figure"].keys()) == [
        "ax3",
        "ax4",
    ]
    assert sorted(list(plotter.ax_dict.keys())) == [
        "ax1",
        "ax2",
        "ax3",
        "ax4",
        "ax5",
        "ax6",
        "ax7",
        "ax8",
    ]
    plotter.identify_axes()  # Helper to add the name of the axis on the plot
    # plt.show()


def test_less_keys_in_subplots_mosaic_params_than_subfigs():
    plotter = NestedGridPlotter(
        fig_params={
            "constrained_layout": True,  # Always use this to prevent overlappings
            "figsize": (10, 10),
        },
        subfigs_params={"nrows": 1, "ncols": 2},
        subplots_mosaic_params={
            "the_left_sub_figure": dict(
                mosaic=[["t-left", "t-left"], ["b-left", "b-right"]],
            ),
        },
    )
    assert list(plotter.subfigs.keys()) == ["the_left_sub_figure"]
    assert list(plotter.grouped_ax_dict.keys()) == ["the_left_sub_figure"]
    assert sorted(list(plotter.grouped_ax_dict["the_left_sub_figure"].keys())) == [
        "b-left",
        "b-right",
        "t-left",
    ]
    assert sorted(list(plotter.ax_dict.keys())) == ["b-left", "b-right", "t-left"]
    plotter.identify_axes()
    # plt.show()


def test_error_more_keys_in_subplots_mosaic_params_than_subfigs():
    with pytest.raises(Exception):
        return NestedGridPlotter(
            fig_params={
                "constrained_layout": True,  # Always use this to prevent overlappings
                "figsize": (10, 10),
            },
            subfigs_params={"nrows": 1, "ncols": 2},
            subplots_mosaic_params={
                "the_left_sub_figure": dict(
                    mosaic=[["tl1", "tl1"], ["bl1", "br1"]],
                ),
                "the_center_sub_figure": dict(
                    mosaic=[["tl2", "tl2"], ["bl2", "br2"]],
                ),
                "the_right_sub_figure": dict(
                    mosaic=[["tl3", "tl3"], ["bl3", "br3"]],
                ),
            },
        )


def test_error_same_axis_names_used_in_multiple_subfigures():
    # Test multiple duplicatedaxis names
    with pytest.raises(Exception):
        return NestedGridPlotter(
            fig_params={
                "constrained_layout": True,  # Always use this to prevent overlappings
                "figsize": (10, 10),
            },
            subfigs_params={"nrows": 1, "ncols": 2},
            subplots_mosaic_params={
                "the_left_sub_figure": dict(
                    mosaic=[["ax11", "ax11"], ["ax12", "ax13"]],
                ),
                "the_right_sub_figure": dict(
                    mosaic=[["ax12", "ax11"], ["ax12", "ax13"]],
                ),
            },
        )

    # Test single duplicatedaxis name
    with pytest.raises(Exception):
        return NestedGridPlotter(
            fig_params={
                "constrained_layout": True,  # Always use this to prevent overlappings
                "figsize": (10, 10),
            },
            subfigs_params={"nrows": 1, "ncols": 2},
            subplots_mosaic_params={
                "the_left_sub_figure": dict(
                    mosaic=[["ax11", "ax11"]],
                ),
                "the_right_sub_figure": dict(
                    mosaic=[["ax21", "ax11"]],
                ),
            },
        )


def test_savefig(tmp_path_factory):
    tmp_folder = tmp_path_factory.mktemp("data")
    plotter = NestedGridPlotter()
    ax = plotter.ax_dict["ax1-1"]
    x = np.linspace(0, 2, 100)  # Sample data.
    ax.plot(x, x, label="linear")
    ax.legend()
    plotter.savefig(tmp_folder.joinpath("test_fig"))


def test_close() -> None:
    plotter = NestedGridPlotter()
    plotter.close()


def gen_complex_example_fig() -> NestedGridPlotter:
    return NestedGridPlotter(
        fig_params={
            "constrained_layout": True,  # Always use this to prevent overlappings
            "figsize": (15, 10),
        },
        subfigs_params={"nrows": 1, "ncols": 2},
        subplots_mosaic_params={
            "the_left_sub_figure": dict(
                mosaic=[["lt1", "lt1"], ["lb1", "rb1"]],
                gridspec_kw=dict(height_ratios=[2, 1], width_ratios=[2, 1]),
                sharey=False,
            ),
            "the_right_sub_figure": dict(
                mosaic=[["l2", "rt2"], ["l2", "bt2"]],
                gridspec_kw=dict(height_ratios=[2, 1], width_ratios=[2, 1]),
                sharey=False,
            ),
        },
    )


def test_get_axis() -> None:
    plotter = gen_complex_example_fig()
    # Get an axis
    assert isinstance(plotter.get_axis("bt2"), Axes)

    with pytest.raises(ValueError, match='The axis "test" does not exists!'):
        plotter.get_axis("test")


def test_get_axes() -> None:
    plotter = gen_complex_example_fig()
    # Get an axis
    for ax in plotter.get_axes(["lt1", "l2", "bt2"]):
        assert isinstance(ax, Axes)

    for ax in plotter.get_axes(["lt1"]):
        assert isinstance(ax, Axes)

    for ax in plotter.get_axes(list(plotter.ax_dict.keys())):
        assert isinstance(ax, Axes)

    with pytest.raises(ValueError, match='The axis "test" does not exists!'):
        plotter.get_axes(["test"])


def test_get_subfigure() -> None:
    plotter = gen_complex_example_fig()
    # Get a subfigure
    assert isinstance(plotter.get_subfigure("the_right_sub_figure"), SubFigure)

    with pytest.raises(ValueError, match='The subfigure "test" does not exists!'):
        plotter.get_subfigure("test")


def test_add_grid_to_all_axes_of_a_subfigure():
    # Create a plot
    plotter = gen_complex_example_fig()
    # Add the grids
    plotter.add_grid_and_tick_prams_to_all_axes(
        subfigure_name="the_left_sub_figure", colors="red", grid_color="red"
    )

    for subfig_name, ax_dict in plotter.grouped_ax_dict.items():
        if subfig_name == "the_left_sub_figure":
            for ax in ax_dict.values():
                assert ax.xaxis.get_major_ticks()[0].gridline.get_visible()
                assert ax.yaxis.get_major_ticks()[0].gridline.get_visible()
        else:
            for ax in ax_dict.values():
                assert not ax.xaxis.get_major_ticks()[0].gridline.get_visible()
                assert not ax.yaxis.get_major_ticks()[0].gridline.get_visible()


def test_add_grid_to_all_axes_of_the_plot():
    # Create a plot
    plotter = gen_complex_example_fig()
    # Add the grids to all subfigures' plots
    plotter.add_grid_and_tick_prams_to_all_axes(
        colors="blue", grid_color="blue", length=5
    )
    for name, ax in plotter.ax_dict.items():
        if name in ["lt1", "lb1"]:
            assert ax.xaxis.get_major_ticks()[0].gridline.get_visible()
            assert ax.yaxis.get_major_ticks()[0].gridline.get_visible()


# Generate a figure and add some data to it
def generate_legend_test_figure() -> NestedGridPlotter:
    _plotter = gen_complex_example_fig()
    x = np.linspace(0, 2, 100)  # Sample data.
    for ax_name, ax in _plotter.ax_dict.items():
        ax.plot(x, x, label=f"linear {ax_name}")  # Plot some data on the axes.
        ax.plot(
            x, x**2, label=f"quadratic {ax_name}"
        )  # Plot more data on the axes...
        ax.plot(x, x**3, label=f"cubic {ax_name}")  # ... and some more.
    return _plotter


def generate_legend_test_figure_common_items() -> NestedGridPlotter:
    _plotter = gen_complex_example_fig()
    x = np.linspace(0, 2, 100)  # Sample data.
    for ax_name, ax in _plotter.ax_dict.items():
        ax.plot(
            x, x, label="the common linear legend item"
        )  # Plot some data on the axes.
        ax.plot(
            x, x**2, label="the common quadratic legend item"
        )  # Plot more data on the axes...
        ax.plot(x, x**3, label="the common cubic legend item")  # ... and some more.
    return _plotter


def test_axis_and_fig_add_legend():
    plotter = generate_legend_test_figure()

    # Test that there are no legend on any axes / figure
    # https://github.com/matplotlib/matplotlib/blob/v3.5.1/lib/matplotlib/figure.py#L942-L1075
    assert plotter.fig.legends == []  # stored as a list for Figure
    for subfig in plotter.subfigs.values():
        assert subfig.legends == []  # stored as a list at the SubFigure level
    for ax_name, ax in plotter.ax_dict.items():
        assert ax.legend_ is None

    # Add some legends and test that it has been correctly added
    for ax_name in plotter.ax_dict.keys():
        plotter.add_axis_legend(ax_name, fontsize=10)
    for ax_name, ax in plotter.ax_dict.items():
        # Handles
        assert len(ax.legend_.legendHandles) == 3
        # Labels
        assert [t._text for t in ax.legend_.texts] == [
            f"linear {ax_name}",
            f"quadratic {ax_name}",
            f"cubic {ax_name}",
        ]

    # Test fig legend
    plotter.add_fig_legend(fontsize=10, ncol=2)
    assert len(plotter.fig.legends) == 1
    all_labels = [t._text for ax in plotter.axes for t in ax.legend_.texts]
    assert sorted([t._text for t in plotter.fig.legends[0].texts]) == sorted(all_labels)


def test_add_fig_legend_with_duplicated_labels_among_axes():
    # Test fig legend with common labels
    plotter = generate_legend_test_figure_common_items()
    plotter.add_fig_legend(fontsize=10)
    assert sorted([t._text for t in plotter.fig.legends[0].texts]) == sorted(
        [
            "the common linear legend item",
            "the common quadratic legend item",
            "the common cubic legend item",
        ]
    )


def test_add_fig_legend_with_empty_figure():
    """Empty figure i.e., no data."""
    plotter = NestedGridPlotter()
    plotter.add_fig_legend(fontsize=10)
    assert len(plotter.fig.legends) == 0


def test_add_fig_legend_multiple_times():
    plotter = generate_legend_test_figure_common_items()
    # Test the fact that only one legend could be added:
    for i in range(3):
        plotter.fig.legend()

    assert len(plotter.fig.legends) == 3

    for i in range(3):
        plotter.add_fig_legend(fontsize=10)
    assert len(plotter.fig.legends) == 1


def test_add_additional_legend_item():
    plotter = generate_legend_test_figure_common_items()
    handle = Line2D([0, 0], [0, 1], color="k", linewidth=3, linestyle="--")
    plotter.add_extra_legend_item("lt1", handle, "My extra legend item")
    plotter.add_axis_legend("lt1")
    plotter.add_fig_legend(fontsize=10, ncol=2)

    ax_labels = [t._text for t in plotter.ax_dict["lt1"].legend_.texts]
    fig_labels = [t._text for t in plotter.fig.legends[0].texts]

    assert ax_labels[-1] == "My extra legend item"
    assert fig_labels[-1] == "My extra legend item"


@pytest.mark.parametrize(
    "loc,expected_exception",
    [
        ("left", does_not_raise()),
        ("right", does_not_raise()),
        ("bottom", does_not_raise()),
        ("top", does_not_raise()),
        ("smth_that_is_not_valid", pytest.raises(ValueError)),
    ],
)
def test_custom_fig_legend_location(loc, expected_exception):
    plotter = gen_complex_example_fig()
    x = np.linspace(0, 2, 100)  # Sample data.
    for ax_name, ax in plotter.ax_dict.items():
        ax.plot(
            x, x, label="the common linear legend item"
        )  # Plot some data on the axes.
        ax.plot(
            x, x**2, label="the common quadratic legend item"
        )  # Plot more data on the axes...
        ax.plot(x, x**3, label="the common cubic legend item")  # ... and some more.

    with expected_exception:
        plotter.add_fig_legend(
            fontsize=10, loc=loc, bbox_x_shift=0.35, bbox_y_shift=0.0
        )

    # TODO: find a way to assert the position of the legend ???


def test_clear_all_axes():
    plotter = gen_complex_example_fig()
    x = np.linspace(0, 2, 100)  # Sample data.
    for ax_name, ax in plotter.ax_dict.items():
        ax.plot(
            x, x, label="the common linear legend item"
        )  # Plot some data on the axes.
        ax.plot(
            x, x**2, label="the common quadratic legend item"
        )  # Plot more data on the axes...
        ax.plot(x, x**3, label="the common cubic legend item")  # ... and some more.

    handle = Line2D([0, 0], [0, 1], color="k", linewidth=3, linestyle="--")
    plotter.add_extra_legend_item("lt1", handle, "My left extra legend item")

    handle = Line2D([0, 0], [0, 1], color="r", linewidth=3, linestyle="--")
    plotter.add_extra_legend_item("l2", handle, "My right extra legend item")

    plotter.add_fig_legend(fontsize=10, loc="top", bbox_x_shift=0.35, bbox_y_shift=0.0)
    plotter.add_fig_legend(
        name="the_left_sub_figure", fontsize=10, bbox_x_shift=0.35, bbox_y_shift=0.0
    )
    plotter.add_fig_legend(
        name="the_right_sub_figure", fontsize=10, bbox_x_shift=0.35, bbox_y_shift=0.0
    )

    for ax_name in plotter.ax_dict.keys():
        assert len(plotter._get_axis_legend_items(ax_name)[0]) != 0

    assert len(plotter.fig.legends) != 0
    for subfig in plotter.subfigs.values():
        assert len(subfig.legends) != 0

    assert len(plotter._additional_handles) != 0
    assert len(plotter._additional_labels) != 0

    # We clear all
    plotter.clear_all_axes()

    for ax_name in plotter.ax_dict.keys():
        assert len(plotter._get_axis_legend_items(ax_name)[0]) == 0

    assert len(plotter.fig.legends) == 0
    for subfig in plotter.subfigs.values():
        assert len(subfig.legends) == 0

    assert len(plotter._additional_handles) == 0
    assert len(plotter._additional_labels) == 0
