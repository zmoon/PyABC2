# Release notes

## v0.1.1 (unreleased)

* Fix loading The Session sets data ({pull}`77`)

## v0.1.0 (2025-07-02)

I've recently cleaned up a few things and added docs ({pull}`68`, {pull}`69`),
but otherwise {mod}`pyabc2` has been pretty much the same for a few years now.
I wanted to preserve this state of the project before making breaking changes.

Compared to [campagnola/pyabc](https://github.com/campagnola/pyabc),
a major inspiration for this project, {mod}`pyabc2` (thus far at least):

```{currentmodule} pyabc2

```

* doesn't really attempt tokenization, just focuses on extracting the melody notes
* takes into account repeats and endings in order to extract the full melody
  ({attr}`Tune.measures`, {meth}`Tune.iter_notes`)
* has separate {class}`Pitch` and {class}`PitchClass` classes
* has {class}`Note` inherit from {class}`Pitch` instead of a token class
* includes tools for fetching tune data from Norbeck, in addition to from The Session
* implements HTML reprs, including using [abcjs](https://www.abcjs.net/)
  to display tunes in the Jupyter notebook
  ({doc}`examples <examples/types>`)
* makes use of type annotations
* adds more methods/properties for pitch/note and key classes
* is available [on PyPI](https://pypi.org/project/pyabc2/)
