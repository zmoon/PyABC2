"""
`abcjs <https://www.abcjs.net/>`__ widget for Jupyter and more.

See examples in :doc:`/examples/widget`.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ipywidgets

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
    svgs = traitlets.List(traitlets.Unicode(), []).tag(sync=True)

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


def interactive(abc: str = "", **kwargs) -> "ipywidgets.Widget":
    """Return a Jupyter widget for interactive use, using ipywidgets."""
    import ipywidgets as ipw

    w = ABCJSWidget(abc=abc, **kwargs)
    w.foreground = "black"

    slider_kws = dict(
        layout={"width": "500px"},
        style={"description_width": "125px"},
    )
    input_box = ipw.Textarea(
        value=None,
        placeholder="Type something",
        layout={"width": "500px", "height": "5rem"},
    )
    width_slider = ipw.IntSlider(
        min=100,
        max=2000,
        value=740,
        description="Staff width (px)",
        **slider_kws,
    )
    line_thickness_slider = ipw.FloatSlider(
        min=-0.4,
        max=2,
        step=0.05,
        value=0,
        description="Line thickness factor",
        **slider_kws,
    )
    scale_slider = ipw.FloatSlider(
        min=0.2,
        max=3,
        value=1,
        description="Scaling factor",
        **slider_kws,
    )
    transpose_slider = ipw.IntSlider(
        min=-24,
        max=24,
        value=0,
        description="Transpose (half steps)",
        **slider_kws,
    )
    foreground_picker = ipw.ColorPicker(
        concise=False,
        description="Foreground color",
        value=w.foreground,
        style={"description_width": "130px"},
    )

    # logo_cbox = ipw.Checkbox(description="Add logo", indent=False)  # currently have to decide at init
    debug_label = ipw.Label(value="Display debug options:", layout={"width": "180px"})
    debug_box_cbox = ipw.Checkbox(description="Box", indent=False)
    debug_grid_cbox = ipw.Checkbox(description="Grid", indent=False)
    debug_input_cbox = ipw.Checkbox(description="Input", indent=False)

    ipw.link((w, "abc"), (input_box, "value"))
    ipw.link((w, "staff_width"), (width_slider, "value"))
    ipw.link((w, "scale"), (scale_slider, "value"))
    ipw.link((w, "line_thickness_increase"), (line_thickness_slider, "value"))
    ipw.link((w, "transpose"), (transpose_slider, "value"))
    ipw.link((w, "foreground"), (foreground_picker, "value"))
    # ipw.link((w, "logo"), (logo_cbox, "value"))
    ipw.link((w, "debug_box"), (debug_box_cbox, "value"))
    ipw.link((w, "debug_grid"), (debug_grid_cbox, "value"))
    ipw.link((w, "debug_input"), (debug_input_cbox, "value"))

    save_name_input = ipw.Text(
        description="Save as",
        value="music.svg",
        placeholder="filename",
    )
    save_overwrite_cbox = ipw.Checkbox(
        description="Overwrite",
        indent=False,
    )
    save_button = ipw.Button(
        description="Save",
        tooltip="Save to SVG",
    )

    def save(_):
        # TODO: HTML option?
        p = Path.cwd() / save_name_input.value
        if not p.suffix.lower() == ".svg":
            p = p.with_suffix(".svg")
        if p.exists() and not save_overwrite_cbox.value:
            raise FileExistsError(f"{p} exists, check 'Overwrite' to replace.")
        if not w.svgs:
            raise ValueError("Nothing to save.")
        elif len(w.svgs) == 1:
            with open(p, "w") as f:
                f.write(w.svgs[0])
        else:
            raise ValueError("Multiple SVGs")

    save_button.on_click(save)

    layout = ipw.VBox(
        [
            input_box,
            width_slider,
            scale_slider,
            line_thickness_slider,
            transpose_slider,
            foreground_picker,
            # logo_cbox,
            w,
            ipw.HBox(
                [
                    save_name_input,
                    save_overwrite_cbox,
                    save_button,
                ],
                # layout={"justify_content": "space-between"},
            ),
            ipw.HBox(
                [
                    debug_label,
                    debug_box_cbox,
                    debug_grid_cbox,
                    debug_input_cbox,
                ]
            ),
        ]
    )

    return layout
