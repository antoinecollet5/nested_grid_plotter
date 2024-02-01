==============
Changelog
==============

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
