"""
abcjs widget for Jupyter and more.
"""

from pathlib import Path

import anywidget

HERE = Path(__file__).parent


class ABCJSWidget(anywidget.AnyWidget):
    _esm = HERE / "index.js"
    _css = HERE / "index.css"