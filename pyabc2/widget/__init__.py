"""
abcjs widget for Jupyter and more.
"""

from pathlib import Path

import anywidget
import traitlets

HERE = Path(__file__).parent


class ABCJSWidget(anywidget.AnyWidget):
    """Display SVG sheet music rendered from ABC notation by abcjs."""

    _esm = HERE / "index.js"
    _css = HERE / "index.css"

    # Input
    abc = traitlets.Unicode("").tag(sync=True)

    # Output
    svgs = traitlets.List(traitlets.Unicode, []).tag(sync=True)

    # Options
    debug_box = traitlets.Bool(False).tag(sync=True)
    debug_grid = traitlets.Bool(False).tag(sync=True)
    debug_input = traitlets.Bool(False).tag(sync=True)
    foreground = traitlets.Unicode(None, allow_none=True).tag(sync=True)
    hide = traitlets.Bool(False).tag(sync=True)
    line_thickness_increase = traitlets.Float(0.0).tag(sync=True)
    logo = traitlets.Bool(False).tag(sync=True)
    scale = traitlets.Float(1.0).tag(sync=True)
    staff_width = traitlets.Integer(740).tag(sync=True)
    transpose = traitlets.Integer(0).tag(sync=True)
