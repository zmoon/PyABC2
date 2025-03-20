"""
abcjs widget for Jupyter and more.
"""

from pathlib import Path

import anywidget
import traitlets

HERE = Path(__file__).parent


class ABCJSWidget(anywidget.AnyWidget):
    _esm = HERE / "index.js"
    _css = HERE / "index.css"

    # Input
    abc = traitlets.Unicode("").tag(sync=True)

    # Output
    svgs = traitlets.List(traitlets.Unicode, []).tag(sync=True)

    # Options
    staff_width = traitlets.Integer(740).tag(sync=True)
    scale = traitlets.Float(1.0).tag(sync=True)
