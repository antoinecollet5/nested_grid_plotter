"""
Test the AnimatedPlotter class.

Note that the tests are very similar to the examples found in the tutorial and
follow the same order.

@author: Antoine COLLET
"""

import itertools
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

import numpy as np
import pytest
from matplotlib import colors
from matplotlib.animation import HTMLWriter
from matplotlib.figure import Figure
from matplotlib.text import Text

from nested_grid_plotter.animated_plotter import AnimatedPlotter, _get_nb_frames

# turns all warnings into errors for this module
# pytestmark = pytest.mark.filterwarnings("error")


@contextmanager
def does_not_raise() -> Generator[None, None, None]:
    yield


@pytest.fixture
def tmp_folder(tmp_path_factory) -> Path:
    """Create a temporary directory"""
    return Path(tmp_path_factory.mktemp("tmp_folder"))


@pytest.mark.filterwarnings("error")
@pytest.mark.parametrize(
    "nb_frames,nb_steps,expected_value,expected_exception",
    [
        (5, 10, 5, does_not_raise()),
        (None, 10, 10, does_not_raise()),
        (
            10,
            5,
            10,
            pytest.raises(
                UserWarning,
                match=re.escape(
                    "The nb_frames (10) required exceeds the number of steps"
                    " available (last dimension of arrays = 5)!"
                    " Some images will be repeated."
                ),
            ),
        ),
    ],
)
def test_get_nb_frames(
    nb_frames: Optional[int], nb_steps: int, expected_value: int, expected_exception
) -> int:
    with expected_exception:
        assert _get_nb_frames(nb_frames, nb_steps) == expected_value


def make_2_frames_plotter() -> AnimatedPlotter:
    return AnimatedPlotter(
        fig_params={"figsize": (10, 5)},
        subplots_mosaic_params={
            "fig0": dict(mosaic=[["ax11", "ax12"]], sharey=True, sharex=True)
        },
    )


def test_init() -> AnimatedPlotter:
    return AnimatedPlotter()


def test_no_animation() -> None:
    """Test the case when no animation has been defined."""
    with pytest.raises(AttributeError, match=r"No animation as been defined !"):
        AnimatedPlotter().animation


def test_animated_multi_plot(tmp_folder) -> None:
    # - Create some 1D data
    # If `x` is provided, it must be for all `y`. While `y` must be a 2d array, `x`
    # can be 1D or 2D.
    x = np.arange(0, 2 * np.pi, 0.1)
    # static
    y = np.sin(x)
    # animated
    nb_frames = 5
    y_animated = np.array([np.sin(x + i / 20) for i in range(nb_frames)]).T
    # Note, the number of frames should be the second dimension

    # other -> varying four times faster and with twice the amplitude
    y2 = y * 2.0
    y2_animated = np.array([np.sin(x + i / 10.0) * 2.0 for i in range(nb_frames)]).T
    y22_animated = np.array([np.sin(x + i / 5.0) * 2.0 for i in range(nb_frames)]).T

    plotter = make_2_frames_plotter()

    # Static plot on both axes
    plotter.ax_dict["ax11"].plot(x, y)
    plotter.ax_dict["ax12"].plot(x, y2)

    # Animated plot on "ax12"
    # x can be 2D but cannot vary (only the first vector given is considered)
    plotter.animated_multi_plot(
        ax_name="ax11",
        data={
            "y_animated (violet)": {"x": x, "y": y_animated, "kwargs": {"c": "violet"}}
        },
        xlabel="My X label",
        ylabel="My Y label",
        title="My awesome title",
    )

    # y must be provided
    with pytest.raises(
        ValueError,
        match=(
            r"Error with data arguments: for key \"y_animated2 \(blue\)\" "
            r"y must be given!"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax12",
            data={
                "y_animated2 (blue)": {"x": x},
            },
            xlabel="My other X label",
            ylabel="My other Y label",
            title="My second awesome title",
        )

    # Animated plot on "ax12"
    # so x can be 1D as well -> simpler
    # multiple lines can be created at once. In that case, the dimensions consistency
    # are checked
    plotter.animated_multi_plot(
        ax_name="ax12",
        data={
            "y_animated2 (blue)": {"x": x, "y": y2_animated},
            "y_animated22 (red)": {
                "x": x,
                "y": y22_animated,
                "kwargs": {"c": "red", "marker": "x", "linestyle": "none"},
            },
        },
        xlabel="My other X label",
        ylabel="My other Y label",
        title="My second awesome title",
    )

    # Add a text animation
    s1 = [f"frame #{i}" for i in range(nb_frames)]
    s2 = [f"time = {i * 60} s" for i in range(nb_frames)]
    plotter.plot_animated_text(
        plotter.ax_dict["ax11"], x=0.01, y=1.8, s=s2, color="red"
    )
    plotter.plot_animated_text(
        plotter.ax_dict["ax12"], x=0.01, y=1.8, s=s1, fontweight="bold"
    )

    # Add legend
    plotter.add_fig_legend()

    # Add title animation
    seq = [f"My fig title @ frame #{i}" for i in range(nb_frames)]
    plotter.subfigs["fig0"].suptitle(seq[0])

    # Change the color, just for fun
    colors = itertools.cycle(("r", "g", "b", "c", "k", "orange"))

    # Define the update function
    def _animate(frame: int) -> List[Text]:
        """Update the text value."""
        # txt.set_text(seq[frame])  # -> to change the text of the title only
        txt: Text = plotter.subfigs["fig0"].suptitle(
            seq[0], fontsize=20, color=next(colors)
        )
        return [
            txt,
        ]

    # Add the update function to the internal mechanic
    plotter.animations_list.append(_animate)

    # Animate the all
    # plotter.close() -> this crashes on github pipelines
    plotter.animate(nb_frames=nb_frames)

    # Save the animation locally on the computer
    fname_html: Path = tmp_folder.joinpath("test1D.html")
    writer: HTMLWriter = HTMLWriter(fps=20, embed_frames=True)
    writer.frame_format = "svg"  # Ensure svg format
    plotter.animation.save(fname_html, writer=writer)


def test_multi_plot_x_vector_exception() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match="When the x vector is provided, it must be for each y vector!",
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"y": np.ones((5, 5))},
                "curve2": {"x": np.ones(5), "y": np.ones((5, 10))},
            },
        )


def test_multi_plot_nb_steps_exception() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Not all given y arrays have the same number of steps (last dimension)!"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"x": np.ones(5), "y": np.ones((5, 5))},
                "curve2": {"x": np.ones(5), "y": np.ones((5, 10))},
            },
        )


def test_1D_exceptions_3() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Not all given x arrays have the same number of steps (last dimension)!"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"x": np.ones((5, 5)), "y": np.ones((5, 10))},
                "curve2": {"x": np.ones(5), "y": np.ones((5, 10))},
            },
        )


def test_1D_exceptions_4() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Not all given y arrays have the same first dimension (n values)!"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"y": np.ones((4, 10))},
                "curve2": {"y": np.ones((5, 10))},
            },
        )


def test_1D_exceptions_5() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Not all given y arrays have the same first dimension (n values)!"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"y": np.ones((4, 10))},
                "curve2": {"y": np.ones((5, 10))},
            },
        )


def test_1D_exceptions_6() -> None:
    plotter: AnimatedPlotter = AnimatedPlotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "x and y must have same first dimension, but have shapes (4,) and (5,)"
        ),
    ):
        plotter.animated_multi_plot(
            ax_name="ax1-1",
            data={
                "curve1": {"x": np.ones(4), "y": np.ones((5, 10))},
                "curve2": {"x": np.ones(5), "y": np.ones((5, 10))},
            },
        )


@pytest.mark.parametrize(
    "is_fig,is_symmetric_cbar,cbar_title,imshow_kwargs,xlabel,ylabel",
    [
        (True, False, None, None, None, None),
        (True, True, "my title", {"vmin": 2.0, "vmax": 5.0}, "xlab", "ylab"),
        (
            False,
            True,
            "my title",
            {"norm": colors.LogNorm(vmin=1e-6, vmax=100.0)},
            "xlab",
            "ylab",
        ),
    ],
)
def test_animated_multi_imshow(
    tmp_folder, is_fig, is_symmetric_cbar, cbar_title, imshow_kwargs, xlabel, ylabel
) -> None:
    plotter = make_2_frames_plotter()

    def f(x, y):
        return np.sin(x) + np.cos(y) + 2

    x = np.linspace(0, 2 * np.pi, 120)
    y = np.linspace(0, 2 * np.pi, 100).reshape(-1, 1)

    nb_frames = 3
    data1 = []
    data2 = []
    for i in range(10):
        data1.append(f(x + np.pi / 20.0 * i, y + np.pi / 20.0 * i))
        data2.append(f(x + np.pi / 20.0 * i, y - np.pi / 20.0 * i))

    # Careful, dimensions are (nx, ny, nt) -> use dstack
    data = {"data1": np.dstack(data1), "data2": np.dstack(data2)}

    if is_fig:
        fig: Optional[Figure] = plotter.fig
    else:
        fig = None

    # Plot it
    plotter.animated_multi_imshow(
        ["ax11", "ax12"],
        data,
        fig=fig,
        nb_frames=nb_frames,
        imshow_kwargs=imshow_kwargs,
        cbar_title=cbar_title,
        xlabel=xlabel,
        ylabel=ylabel,
        is_symmetric_cbar=is_symmetric_cbar,
    )
    # plotter.close() -> this crashes on github pipelines
    plotter.animate(nb_frames=nb_frames)

    # Save the animation locally on the computer
    fname_html: Path = tmp_folder.joinpath("test2D.html")
    writer: HTMLWriter = HTMLWriter(fps=20, embed_frames=True)
    writer.frame_format = "svg"  # Ensure svg format
    plotter.animation.save(fname_html, writer=writer)


def test_animated_multi_imshow_nb_steps_exception() -> None:
    plotter = make_2_frames_plotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            "Not all given arrays have the same number of steps (last dimension)!"
        ),
    ):
        plotter.animated_multi_imshow(
            ax_names=["ax12", "ax12"],
            data={
                "data1": np.random.random((5, 5, 5)),
                "data2": np.random.random((5, 5, 6)),
            },
            nb_frames=5,
        )


def test_multi_imshow_animated_dimension_exception() -> None:
    plotter = make_2_frames_plotter()

    with pytest.raises(
        ValueError,
        match=re.escape(
            'The given data for "data2" has shape (5, 5) '
            "whereas it should be three dimensional!"
        ),
    ):
        plotter.animated_multi_imshow(
            ax_names=["ax12", "ax12"],
            data={
                "data1": np.random.random((5, 5, 5)),
                "data2": np.random.random((5, 5)),
            },
            nb_frames=5,
        )
