"""
Tests for the imshow sub module.

Note that the tests are very similar to the examples found in the tutorial and
follow the same order.

@author: Antoine COLLET
"""

import re
from contextlib import contextmanager
from typing import Any, Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import colors
from matplotlib.axes import Axes  # Just for liting
from matplotlib.figure import Figure

from nested_grid_plotter.imshow import (
    _apply_default_colorbar_kwargs,
    _apply_default_imshow_kwargs,
    _check_axes_and_data_consistency,
    _norm_data_and_cbar,
    add_2d_grid,
    multi_imshow,
)


@contextmanager
def does_not_raise():
    yield


def get_2_axes() -> Tuple[Figure, Tuple[Axes, Axes]]:
    return plt.subplots(ncols=2)


def test_apply_default_imshow_kwargs_none() -> None:
    # test with an empty dict
    res1 = _apply_default_imshow_kwargs(None)
    assert isinstance(res1.pop("norm"), colors.Normalize)
    assert res1 == {
        "interpolation": "nearest",
        "cmap": "bwr",
        "aspect": "auto",
        "origin": "lower",
    }


@pytest.mark.parametrize("key", ["vmin", "vmax", "norm"])  # tiff is too heavy
def test_apply_default_imshow_kwargs_norm_behavior(key) -> None:
    test_dict = {"cmap": "viridis", key: 52.0, "smth_else": 2}
    assert _apply_default_imshow_kwargs(test_dict) == {
        "interpolation": "nearest",
        "cmap": "viridis",
        "aspect": "auto",
        "origin": "lower",
        key: 52.0,
        "smth_else": 2,
    }


def test_apply_default_colorbar_kwargs_none() -> None:
    # test with an empty dict
    fig, axes = plt.subplots(nrows=2)
    res1 = _apply_default_colorbar_kwargs(None, axes)
    assert (res1.pop("ax") == np.array(axes)).all()
    assert res1 == {"orientation": "vertical", "aspect": 20}


def test_apply_default_colorbar_kwargs_norm_behavior() -> None:
    fig, axes = plt.subplots(nrows=2)
    test_dict = {
        "ax": axes[0],
        "smth_else": 2,
        "aspect": 50,
    }
    assert _apply_default_colorbar_kwargs(test_dict, axes) == {
        "orientation": "vertical",
        "aspect": 50,
        "ax": axes[0],
        "smth_else": 2,
    }


def test_add_2d_grid() -> None:
    fig, axes = get_2_axes()

    # With no kwargs
    add_2d_grid(axes[0], nx=10, ny=10)
    # with kwargs
    add_2d_grid(axes[1], nx=10, ny=10, kwargs={"color": "red", "linestyle": "--"})


@pytest.mark.parametrize(
    "is_symmetric,imshow_kwargs",
    [(False, {}), (False, {}), (True, {}), (True, {})],
)  # tiff is too heavy
def test_normalize_data_and_cbar(
    is_symmetric: bool, imshow_kwargs: Dict[str, Any]
) -> None:
    fig, (ax1, ax2) = get_2_axes()

    data1 = np.random.uniform(low=-1.0, high=1.0, size=(10, 10))
    data2 = np.random.uniform(low=0.5, high=4.0, size=(10, 10))

    im1 = ax1.imshow(data1)
    assert 1.0 > im1.norm.vmin > -1.0
    assert 1.0 > im1.norm.vmax > -1.0
    im2 = ax2.imshow(data2)
    assert 4.0 > im2.norm.vmin > 0.5
    assert 4.0 > im2.norm.vmax > 0.5
    _norm_data_and_cbar(
        [im1, im2], [data1, data2], imshow_kwargs, is_symmetric_cbar=is_symmetric
    )
    assert im1.norm.vmax == im2.norm.vmax
    assert im1.norm.vmin == im2.norm.vmin
    assert im1.norm.vmax > 1.0
    assert 0.5 > im2.norm.vmin

    if is_symmetric:
        assert im1.norm.vmin == -im1.norm.vmax == -np.max(data2)


@pytest.mark.parametrize(
    "data,expected_exception",
    [
        ({"ax1": None, "ax2": None}, does_not_raise()),
        (
            {"ax1": None},
            pytest.raises(
                ValueError,
                match=re.escape(
                    r"The number of axes (2), does not match the number of data (1)!"
                ),
            ),
        ),
    ],
)
def test_check_axes_and_data_consistency(data, expected_exception) -> None:
    fig, (ax1, ax2) = get_2_axes()
    with expected_exception:
        _check_axes_and_data_consistency([ax1, ax2], data)


@pytest.mark.parametrize(
    "is_symmetric_cbar,cbar_title,imshow_kwargs,xlabel,ylabel,expected_exception",
    [
        (False, None, None, None, None, does_not_raise()),
        (
            True,
            "my title",
            {"vmin": 2.0, "vmax": 5.0},
            "xlab",
            "ylab",
            does_not_raise(),
        ),
        (
            True,
            "my title",
            {"norm": colors.LogNorm(vmin=1e-6, vmax=100.0)},
            "xlab",
            "ylab",
            pytest.warns(
                UserWarning,
                match=(
                    "You used a LogNorm norm instance which is incompatible with a"
                    " symmetric colorbar. Symmetry is ignored. Use SymLogNorm for"
                    " symmetrical logscale color bar."
                ),
            ),
        ),
    ],
)
def test_multi_imshow(
    is_symmetric_cbar, cbar_title, imshow_kwargs, xlabel, ylabel, expected_exception
) -> None:
    fig, axes = get_2_axes()
    data = {
        "data1": np.random.uniform(low=1.0, high=2.0, size=(10, 10)),
        "data2": np.random.uniform(low=0.5, high=4.0, size=(10, 10)),
    }

    with expected_exception:
        multi_imshow(
            axes,
            fig,
            data,
            is_symmetric_cbar=is_symmetric_cbar,
            cbar_title=cbar_title,
            imshow_kwargs=imshow_kwargs,
            xlabel=xlabel,
            ylabel=ylabel,
        )


def test_multi_imshow_exception() -> None:
    fig, axes = get_2_axes()
    data = {
        "data1": np.random.uniform(low=1.0, high=2.0, size=(10, 10, 10)),
        "data2": np.random.uniform(low=0.5, high=4.0, size=(10, 10)),
    }

    with pytest.raises(
        ValueError,
        match='The given data for "data1" has dimension'
        " 3 whereas it should be two dimensional!",
    ):
        multi_imshow(axes, fig, data)
