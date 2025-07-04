# PyABC2

Python library for working with melodies in [ABC notation](https://abcnotation.com/).

```{module} pyabc2

```

```{figure} https://user-images.githubusercontent.com/15079414/195207144-83df651a-6fe9-44b1-b7bc-e4aced14a2aa.png
:alt: Polar tune plot for "For the Love of Music" by Liz Carroll

This polar axis plot combines melody trajectory and note histogram.
Each ring represents an octave (outer = higher).
The trajectory changes color with progression through the tune
(dark blue/purple to light yellow).
{ref}`polar-tune-plot` shows how the plot is generated,
with the tune itself shown {doc}`at the top <examples/plots>`.
```

## Getting started

Install from PyPI:
```
pip install pyabc2
```

Then look at the [example notebooks](examples/types.ipynb).

If you have a feature request or find a bug, feel free to open an issue [on GitHub](https://github.com/zmoon/PyABC2/issues).
To contribute code to this project, see the [instructions for developers](dev.md).

## Credits

Inspired in part by and some portions based on [PyABC](https://github.com/campagnola/pyabc) (`pyabc`; [MIT License](https://github.com/campagnola/pyabc/blob/master/LICENSE.txt)), hence "PyABC2" and the package name `pyabc2`. No relation to [this pyabc](https://github.com/icb-dcm/pyabc) that is on PyPI.

---

```{toctree}
:caption: Examples
:hidden:

examples/types.ipynb
examples/modes.ipynb
examples/sources.ipynb
examples/plots.ipynb
```

```{toctree}
:caption: Reference
:hidden:

api.rst
changes.md
dev.md
GitHub <https://github.com/zmoon/PyABC2>
```

```{nb-exec-table}

```
