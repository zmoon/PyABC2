import pytest

from pyabc2.sheet import svg, svg_to

HAVE_CAIROSVG = True
try:
    import cairosvg  # noqa: F401
except (ImportError, OSError):
    # OSError raised if cairosvg is installed but fails to find the cairo library
    HAVE_CAIROSVG = False


@pytest.mark.skipif(not HAVE_CAIROSVG, reason="cairosvg is not available")
def test_svg_to_ignored_args():
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

    with pytest.warns(
        UserWarning,
        match="Keyword 'write_to' is not supported and will be ignored.",
    ):
        png_bytes = svg_to(svg_str, "PNG", write_to="asdf")

    assert isinstance(png_bytes, bytes)
