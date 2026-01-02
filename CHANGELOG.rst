==============
Changelog
==============

2.0.0 (2026-01-02)
------------------

* IMP: drop support for python 3.7
* IMP: support for numpy>2 and python up to 3.14.
* IMP: update the packaging system (pyproject.toml).
* DOCS: better docstring and documentations
* IMP: support for nested subfigures and subsequent revision of the initializer
  interface. The `__init__` method of `NestedGridPlotter` and child classes now takes
  two arguments of types Figure and Builder. `SubfigsBuilder`,
  `SubplotsMosaicBuilder` for more flexibility, code linting and auto-completion
  as well as improved documentation. The tutorials and tests have been updated.
* IMP: deprecation of plotter's `subfigs` attribute which is replaced by
  `grouped_sf_dict` and the flatten version `sf_dict`.
* TESTS: use of `pre-commit`, `ruff` and `ty` for linting, type checking and formatting.
* ENH: add a `Plotter` alias for `NestedGridPlotter`.
* ENH: add a `axes_names` properties for `Plotter`.
* FIX: when saving a figure, make sure that if a fig legend as been added, it won't be cutoff by the figure box
* ENH: add a `add_axis_legend_outside_frame` method to `Plotter`.
* FIX: in `multi_imshow`,  make sure that the largest image is displayed last (just in case sharex or sharey is active) to avoid shrinking the image.
* ENH: in `AnimatedPlotter` class, add a `save_animation` method that correctly handles legends.

1.2.0 (2024-06-12)
------------------

* IMP: `add_xaxis_twin_as_date` is now deprecated and replaced by the more
  flexible `ticklabels_to_datetime` and `add_twin_axis_as_datetime`
  functions. The tutorials and tests have been updated.
* IMP: `make_x_axes_symmetric_zero_centered` and
  `make_x_axes_symmetric_zero_centered` have now possibility to ensure minimum
  symmetric axis limits through the `min_xlims` and `min_ylims` keywords respectively.

1.1.2 (2024-04-27)
------------------

* FIX: bbox_extra_artists when using savefig method.

1.1.1 (2024-03-22)
------------------

* ENH: Add a `get_axes` interface to `NestedGridPlotter` class.
* ENH: Provide a `add_letter_to_frames` utility function.
* FIX: RunTimeError Can not put single artist in more than one figure when using
* NestedGridPlotter `add_fig_legend` method and using the main figure.

1.0.1 (2024-03-08)
------------------

* FIX: Prevent figures an subfigures legend cut-off by th figure box when saving images
  to disk.

1.0.0 (2024-01-31)
------------------

* FIX: Typo = symetry to symmetry in keywords.
* FIX: Colorbar scaling = now supports any norm and some duplication has been removed,
  some warnigns added.

0.1.2 (2023-12-03)
------------------

* FIX: Selection of data in animations - when the amount of data is
  larger than the number of frames. The fix ensures that the first frame
  is the first data element and that the last frame is the last data
  element, all other frames matching evenly spaced data element in between.
* DOCS: update animated_plotters.ipynb notebook

0.1.1 (2023-11-20)
------------------

* Add utilities `align_x_axes`, `align_x_axes_on_values` and
  `make_x_axes_symmetric_zero_centered`.
* Remove the default italic styles from titles and axis labels.
* Add a DOI (zenodo)

0.1.0 (2023-06-30)
------------------

* First release on PyPI.
