import pytest

from pyabc2.abcjs.headless import svg, svg_to

HAVE_CAIROSVG = True
try:
    import cairosvg  # noqa: F401
except (ImportError, OSError):
    # OSError raised if cairosvg is installed but fails to find the cairo library
    HAVE_CAIROSVG = False


def test_svg_to():
    abc = """\
    ABCD
    """
    # Note: the indent is ignored by abcjs

    svg_str = svg(
        abc,
        scale=3,
        staff_width=200,
        foregroundColor="blue",
        lineThickness=0.2,
    )
    assert isinstance(svg_str, str)

    if HAVE_CAIROSVG:
        with pytest.warns(
            UserWarning,
            match="Keyword 'write_to' is not supported and will be ignored.",
        ):
            png_bytes = svg_to(svg_str, "PNG", write_to="asdf")

        assert isinstance(png_bytes, bytes)

        with pytest.raises(
            ValueError,
            match="Unsupported format: 'asdf'",
        ):
            _ = svg_to(svg_str, "asdf")

    else:
        with pytest.raises(
            RuntimeError,
            match="The 'cairosvg' package is required to convert SVG to other formats.",
        ):
            _ = svg_to(svg_str, "PNG")
