"""
Test the utilities.

Note that the tests are very similar to the examples found in the tutorial and
follow the same order.

@author: Antoine COLLET
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.animation import HTMLWriter
from matplotlib.axes import Axes  # Just for liting

import nested_grid_plotter as ngp


@pytest.fixture
def tmp_folder(tmp_path_factory):
    """Create a temporary directory"""
    return tmp_path_factory.mktemp("tmp_folder")


def test_get_line_style() -> None:
    ngp.get_line_style("solid")


def create_animation() -> animation:
    fig, ax = plt.subplots()

    x = np.arange(0, 2 * np.pi, 0.01)
    (line,) = ax.plot(x, np.sin(x))

    def animate(i):
        line.set_ydata(np.sin(x + i / 20))  # update the data.
        return (line,)

    return animation.FuncAnimation(fig, animate, interval=10, blit=True, save_count=20)


@pytest.mark.parametrize("frame_format", ["png", "jpeg", "svg"])  # tiff is too heavy
def test_extract_frames(frame_format, tmp_folder) -> None:
    ani = create_animation()

    fname = tmp_folder.joinpath("myfile.html")
    writer = HTMLWriter(fps=10, embed_frames=True)
    writer.frame_format = frame_format  # Ensure svg format
    ani.save(fname, writer=writer)

    # With a given path
    target_path = tmp_folder.joinpath("exported_figures")
    ngp.extract_frames_from_embedded_html_animation(
        fname,
        target_path=target_path,
    )

    assert len(list((target_path.glob(f"**/*.{frame_format}")))) == 20

    # With no path
    ngp.extract_frames_from_embedded_html_animation(
        fname,
        # target_path=target_path,
    )

    expected_path = Path(fname).parent.joinpath(Path(fname).stem)
    assert len(list((expected_path.glob(f"**/*.{frame_format}")))) == 20


def test_make_patch_spines_invisible():
    plotter = ngp.NestedGridPlotter()
    ax = plotter.ax_dict["ax1-1"]
    ngp.add_grid_and_tick_prams_to_axis(ax)
    ngp.make_patch_spines_invisible(ax)


def badfname():
    return "#6262%%this?is#\\my=plot*///name(km/h)"


@pytest.mark.parametrize(
    "test_input,repchar,expected",
    [
        (badfname(), " ", "6262 this is my plot name(km h)"),
        (badfname(), "_", "6262_this_is_my_plot_name(km_h)"),
        (badfname(), "-", "6262-this-is-my-plot-name(km-h)"),
    ],
)
def test_replace_bad_path_characters(test_input, repchar, expected):
    assert ngp.replace_bad_path_characters(test_input, repchar) == expected


def gen_complex_example_fig() -> ngp.NestedGridPlotter:
    return ngp.NestedGridPlotter(
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


def test_add_grid_to_specific_axes_of_the_plot():
    # Create a plot
    plotter = gen_complex_example_fig()

    # Test that there are no grid before the plot
    for name, ax in plotter.ax_dict.items():
        assert not ax.xaxis.get_major_ticks()[0].gridline.get_visible()
        assert not ax.yaxis.get_major_ticks()[0].gridline.get_visible()

    # Add a grid to specific axes
    ngp.add_grid_and_tick_prams_to_axis(plotter.ax_dict["lt1"])
    ngp.add_grid_and_tick_prams_to_axis(
        plotter.ax_dict["lb1"], colors="red", grid_color="red"
    )

    # Test that the grids have been correctly added
    for name, ax in plotter.ax_dict.items():
        if name in ["lt1", "lb1"]:
            assert ax.xaxis.get_major_ticks()[0].gridline.get_visible()
            assert ax.yaxis.get_major_ticks()[0].gridline.get_visible()
        else:
            assert not ax.xaxis.get_major_ticks()[0].gridline.get_visible()
            assert not ax.yaxis.get_major_ticks()[0].gridline.get_visible()


def test_make_ticks_overlapping_axis_frame_invisible():
    # Create a plot
    plotter = gen_complex_example_fig()

    ax_name = "lt1"
    ax = plotter.ax_dict[ax_name]
    # Add a grid to a specific ax
    ngp.add_grid_and_tick_prams_to_axis(ax)
    ngp.make_ticks_overlapping_axis_frame_invisible(ax)

    # Test that the ticks have been hidden correctly
    # For the x axis
    xticks = ax.get_xticks()
    xlines = ax.xaxis.get_ticklines()
    xlim = ax.get_xlim()
    if xticks[0] == xlim[0]:
        assert not xlines[0].get_visible()  # Most left tick of the bottom edge
        assert not xlines[1].get_visible()  # Most right tick of the bottom edge
    if xticks[-1] == xlim[-1]:
        assert not xlines[-2].get_visible()  # Most left tick of the top edge
        assert not xlines[-1].get_visible()  # Most right tick of the top edge

    # For the y axis
    yticks = ax.get_yticks()
    ylines = ax.yaxis.get_ticklines()
    ylim = ax.get_ylim()
    if yticks[0] == ylim[0]:
        assert not ylines[0].get_visible()  # Bottom tick of the left edge
        assert not ylines[1].get_visible()  # Bottom tick of the right edge
    if yticks[-1] == ylim[-1]:
        assert not ylines[-2].get_visible()  # Top tick of the left edge
        assert not ylines[-1].get_visible()  # Top tick of the right edge


def test_hide_axis_ticklabels():
    # Create a plot
    plotter = gen_complex_example_fig()

    ax = plotter.ax_dict["l2"]
    assert len(ax.get_xticklabels()) != 0
    assert len(ax.get_yticklabels()) != 0
    ngp.hide_axis_ticklabels(ax, "x")
    ngp.hide_axis_ticklabels(ax, "y")
    assert len(ax.get_xticklabels()) == 0
    assert len(ax.get_yticklabels()) == 0

    ax = plotter.ax_dict["rt2"]
    assert len(ax.get_xticklabels()) != 0
    assert len(ax.get_yticklabels()) != 0
    ngp.hide_axis_ticklabels(ax, "both")
    assert len(ax.get_xticklabels()) == 0
    assert len(ax.get_yticklabels()) == 0


def test_hide_axis_spines():
    # Create a plot
    plotter = gen_complex_example_fig()
    ax = plotter.ax_dict["bt2"]

    # Remove the spines in plot 'bt2'
    ngp.hide_axis_spine(ax, loc="top")
    ngp.hide_axis_spine(ax, loc="right")
    ngp.hide_axis_spine(ax, loc="left")
    ngp.hide_axis_spine(ax, loc="bottom")

    # Create a plot
    plotter = gen_complex_example_fig()
    ngp.hide_axis_spine(plotter.ax_dict["bt2"], loc="all")


# Create a function to plot the data on one axis
def plotLines(
    x: np.ndarray, y1: np.ndarray, y2: np.ndarray, y3: np.ndarray, ax: Axes
) -> List[Axes]:
    ax.plot(x, y1, "b-")
    ax.tick_params("y", colors="b")

    tax1 = ax.twinx()
    tax1.plot(x, y2, "r-")
    tax1.tick_params("y", colors="r")

    tax2 = ax.twinx()
    tax2.spines["right"].set_position(("axes", 1.2))
    # make_patch_spines_invisible(tax2)
    tax2.spines["right"].set_visible(True)
    tax2.plot(x, y3, "g-")
    tax2.tick_params("y", colors="g")

    ax.grid(True, axis="both")

    return [ax, tax1, tax2]


# Create a function to plot the data on one axis
def plotLines2(
    x1: np.ndarray, x2: np.ndarray, x3: np.ndarray, y: np.ndarray, ax: Axes
) -> List[Axes]:
    ax.plot(x1, y, "b-")
    ax.tick_params("y", colors="b")

    tax1 = ax.twiny()
    tax1.plot(x2, y, "r-")
    tax1.tick_params("y", colors="r")

    tax2 = ax.twiny()
    tax2.spines["right"].set_position(("axes", 1.2))
    # make_patch_spines_invisible(tax2)
    tax2.spines["right"].set_visible(True)
    tax2.plot(x3, y, "g-")
    tax2.tick_params("y", colors="g")

    ax.grid(True, axis="both")

    return [ax, tax1, tax2]


def test_align_x_axes():
    # craft some data to plot
    y = np.arange(20)
    x1 = np.sin(y)
    x2 = y / 1000 + np.exp(y)
    x3 = y + y**2 / 3.14

    plt.rcParams.update({"font.size": 10})
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (14, 6)},
        subfigs_params={"ncols": 3},
    )

    # Left plot: No alignment.
    ax1 = plotter.ax_dict["ax1-1"]
    axes1 = plotLines2(x1, x2, x3, y, ax1)
    ax1.set_title("No alignment")

    assert axes1[0].get_xticks().size != axes1[1].get_xticks().size

    # Mid plot: Aligned at (approximately) the lower bound of each y axis.
    ax2 = plotter.ax_dict["ax1-2"]
    axes2 = plotLines2(x1, x2, x3, y, ax2)
    ngp.align_x_axes(axes2)
    ax2.set_title("Default alignment")

    assert (
        axes2[0].get_xticks().size
        == axes2[1].get_xticks().size
        == axes2[2].get_xticks().size
    )

    # Right plot: Aligned at specified values: 0 for blue, 2.2*1e8 for red, and 44 for
    # green. Those are chosen arbitrarily for the example.
    ax3 = plotter.ax_dict["ax1-3"]
    axes3 = plotLines2(x1, x2, x3, y, ax3)

    # test the case with no arguments:
    ngp.align_x_axes_on_values(
        axes3
    )  # This is not the bast behavior ever, but it should pass
    # test the case when incorrect number of values is given
    with pytest.raises(ValueError):
        ngp.align_x_axes_on_values(axes3, [0, 2.2 * 1e8])

    ngp.align_x_axes_on_values(axes3, [0, 2.2 * 1e8, 44])
    ax3.set_title("Specified alignment")

    assert (
        axes3[0].get_xticks().size
        == axes3[1].get_xticks().size
        == axes3[2].get_xticks().size
    )
    pos = int(np.where(axes3[0].get_xticks() == 0.0)[0][0])
    assert (axes3[1].get_xticks()[pos] - 22 * 1e8) < 0.00001
    assert axes3[2].get_xticks()[pos] == 44.0


def test_align_y_axes():
    # craft some data to plot
    x = np.arange(20)
    y1 = np.sin(x)
    y2 = x / 1000 + np.exp(x)
    y3 = x + x**2 / 3.14

    plt.rcParams.update({"font.size": 10})
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (14, 6)},
        subfigs_params={"ncols": 3},
    )

    # Left plot: No alignment.
    ax1 = plotter.ax_dict["ax1-1"]
    axes1 = plotLines(x, y1, y2, y3, ax1)
    ax1.set_title("No alignment")

    assert axes1[0].get_yticks().size != axes1[1].get_yticks().size

    # Mid plot: Aligned at (approximately) the lower bound of each y axis.
    ax2 = plotter.ax_dict["ax1-2"]
    axes2 = plotLines(x, y1, y2, y3, ax2)
    ngp.align_y_axes(axes2)
    ax2.set_title("Default alignment")

    assert (
        axes2[0].get_yticks().size
        == axes2[1].get_yticks().size
        == axes2[2].get_yticks().size
    )

    # Right plot: Aligned at specified values: 0 for blue, 2.2*1e8 for red, and 44 for
    # green. Those are chosen arbitrarily for the example.
    ax3 = plotter.ax_dict["ax1-3"]
    axes3 = plotLines(x, y1, y2, y3, ax3)
    # test the case with no arguments:
    ngp.align_y_axes_on_values(
        axes3
    )  # This is not the bast behavior ever, but it should pass
    # test the case when incorrect number of values is given
    with pytest.raises(ValueError):
        ngp.align_y_axes_on_values(axes3, [0, 2.2 * 1e8])

    ngp.align_y_axes_on_values(axes3, [0, 2.2 * 1e8, 44])
    ax3.set_title("Specified alignment")

    assert (
        axes3[0].get_yticks().size
        == axes3[1].get_yticks().size
        == axes3[2].get_yticks().size
    )
    pos = int(np.where(axes3[0].get_yticks() == 0.0)[0][0])
    assert (axes3[1].get_yticks()[pos] - 22 * 1e8) < 0.00001
    assert axes3[2].get_yticks()[pos] == 44.0


def test_make_x_axes_symmetric_zero_centered():
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (15, 5)},
        subfigs_params={"ncols": 3},
    )

    # Make some data
    np.random.seed(1)
    # data1 = np.random.normal(0,1,20)
    x_data1 = np.random.rand(20) - 3
    x_data2 = np.random.rand(20)
    y_data = np.arange(x_data1.size)
    xy = np.zeros(20)

    ax1 = plotter.ax_dict["ax1-1"]
    ax1_twin = ax1.twiny()
    ax1.plot(x_data1, y_data, label="data1")
    ax1_twin.plot(x_data2, y_data, c="r", label="data2")
    ax1.set_title("No alignment")

    assert ax1.get_xlim()[0] != -ax1.get_xlim()[1]
    assert ax1_twin.get_xlim()[0] != -ax1_twin.get_xlim()[1]

    ax2 = plotter.ax_dict["ax1-2"]
    ax2_twin = ax2.twiny()
    ax2.plot(x_data1, y_data, label="data1")
    ax2.plot(xy, y_data, linestyle="--")
    ax2_twin.plot(x_data2, y_data, c="r", label="data2")
    ngp.align_x_axes_on_values(
        [ax2, ax2_twin], [0.0, 0.0]
    )  # Works for more than 2 axes
    ax2.set_title("Specific alignment at y=0.0, no symmetry")

    ax3 = plotter.ax_dict["ax1-3"]
    ax3_twin = ax3.twinx()
    ax3.plot(x_data1, y_data, label="data1")
    ax3.plot(xy, y_data, linestyle="--")
    ax3_twin.plot(x_data2, y_data, c="r", label="data2")
    ngp.make_x_axes_symmetric_zero_centered(
        [ax3, ax3_twin]
    )  # Works for more than 2 axes
    ax3.set_title("Specific alignment at y=0.0, with symmetry")

    assert ax3.get_xlim()[0] == -ax3.get_xlim()[1]
    assert ax3_twin.get_xlim()[0] == -ax3_twin.get_xlim()[1]

    plotter.add_fig_legend(fontsize=10, ncol=2)


def test_make_y_axes_symmetric_zero_centered():
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (15, 5)},
        subfigs_params={"ncols": 3},
    )

    # Make some data
    np.random.seed(1)
    # data1 = np.random.normal(0,1,20)
    data1 = np.random.rand(20) - 3
    data2 = np.random.rand(20)
    xy = np.zeros(20)

    ax1 = plotter.ax_dict["ax1-1"]
    ax1_twin = ax1.twinx()
    ax1.plot(data1, label="data1")
    ax1_twin.plot(data2, c="r", label="data2")
    ax1.set_title("No alignment")

    assert ax1.get_ylim()[0] != -ax1.get_ylim()[1]
    assert ax1_twin.get_ylim()[0] != -ax1_twin.get_ylim()[1]

    ax2 = plotter.ax_dict["ax1-2"]
    ax2_twin = ax2.twinx()
    ax2.plot(data1, label="data1")
    ax2.plot(xy, linestyle="--")
    ax2_twin.plot(data2, c="r", label="data2")
    ngp.align_y_axes_on_values(
        [ax2, ax2_twin], [0.0, 0.0]
    )  # Works for more than 2 axes
    ax2.set_title("Specific alignment at y=0.0, no symmetry")

    ax3 = plotter.ax_dict["ax1-3"]
    ax3_twin = ax3.twinx()
    ax3.plot(data1, label="data1")
    ax3.plot(xy, linestyle="--")
    ax3_twin.plot(data2, c="r", label="data2")
    ngp.make_y_axes_symmetric_zero_centered(
        [ax3, ax3_twin]
    )  # Works for more than 2 axes
    ax3.set_title("Specific alignment at y=0.0, with symmetry")

    assert ax3.get_ylim()[0] == -ax3.get_ylim()[1]
    assert ax3_twin.get_ylim()[0] == -ax3_twin.get_ylim()[1]

    plotter.add_fig_legend(fontsize=10, ncol=2)


def test_add_xaxis_twin_as_date() -> None:
    plotter: ngp.NestedGridPlotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (15, 5)},
        subfigs_params={"ncols": 3},
    )

    # Plot the data
    ax1: Axes = plotter.ax_dict["ax1-1"]
    ax1.plot(np.cumsum(0.004 + 0.04 * np.random.randn(100, 5)))
    ax1.set_title("A timeseries with daily data")
    ax1.set_xlabel("Number of days")

    # Add a date x axis
    ngp.add_xaxis_twin_as_date(
        ax1,
        first_date=datetime(2022, 1, 6),
        time_units="days",
        time_format="%d-%m-%Y",
        spine_outward_position=38,
    )

    # Add a date x axis
    ngp.add_xaxis_twin_as_date(
        ax1,
        first_date=datetime(2022, 1, 6),
        time_units="days",
        time_format="%m-%Y",
        spine_outward_position=78,
    )

    # Plot the data
    ax2: Axes = plotter.ax_dict["ax1-2"]
    ax2.plot(np.cumsum(0.004 + 0.04 * np.random.randn(10, 5)))
    ax2.set_title("A timeseries with monthly data")
    ax2.set_xlabel("Number of months")

    # Add a date x axis
    ngp.add_xaxis_twin_as_date(
        ax2,
        first_date=datetime(2022, 1, 6),
        time_units="months",
        time_format="%m-%Y",
        spine_outward_position=38,
    )

    # Plot the data
    ax3: Axes = plotter.ax_dict["ax1-3"]
    ax3.plot(np.cumsum(0.004 + 0.04 * np.random.randn(5, 5)))
    ax3.set_title("A timeseries with yealy data")
    ax3.set_xlabel("Number of years")

    # Add a date x axis
    ax3 = ngp.add_xaxis_twin_as_date(
        ax3,
        first_date=datetime(2022, 1, 6),
        time_units="years",
        time_format="%Y",
        spine_outward_position=38,
    )

    # Add a date x axis
    with pytest.raises(
        ValueError,
        match=re.escape(
            "time_units should be in ['days', 'd', 'months', 'm', 'years', 'y']"
        ),
    ):
        ax3 = ngp.add_xaxis_twin_as_date(
            ax3,
            first_date=datetime(2022, 1, 6),
            time_units="jours",
            time_format="%Y",
            spine_outward_position=38,
        )


def test_add_letter_to_frames_less26axes() -> None:
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (10, 10)},
        subfigs_params={"ncols": 3, "nrows": 3},
    )
    ngp.add_letter_to_frames(plotter.axes)


def test_add_letter_to_frames_more26axes() -> None:
    plotter = ngp.NestedGridPlotter(
        fig_params={"constrained_layout": True, "figsize": (10, 10)},
        subfigs_params={"ncols": 7, "nrows": 7},
    )
    ngp.add_letter_to_frames(plotter.axes)
