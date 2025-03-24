import datetime
import os
from pathlib import Path
from textwrap import indent

HERE = Path(__file__).parent

ALWAYS_BUILD = os.getenv("PYABC_ALWAYS_BUILD_NPM_PACKAGE", "0") == "1"


def build():
    try:
        from nodejs_wheel import npm
    except ImportError as e:
        raise RuntimeError(
            "The 'nodejs-wheel-binaries' package is required "
            "to render sheet music in the background with abcjs via Node.js. "
            "It is included with the pyabc2 'sheet' extra."
        ) from e

    rc = npm(["install", HERE.as_posix()])
    if rc != 0:
        raise RuntimeError("Build failed")


def _maybe_build():
    now = datetime.datetime.now().timestamp()
    package_lock = HERE / "package-lock.json"
    if ALWAYS_BUILD or (
        package_lock.exists() and now - package_lock.stat().st_mtime > 7 * 24 * 3600
    ):
        build()


def svg(
    abc: str,
    *,
    # Keep names consistent with the widget!
    scale: float = 1.0,
    staff_width: int = 600,
    **kwargs,
) -> str:
    """Render ABC notation to SVG sheet music using abcjs.

    Parameters
    ----------
    abc
        The ABC notation to render.
    **kwargs
        Additional abcjs options that haven't been explicitly defined here
        in the signature.
        https://paulrosen.github.io/abcjs/visual/render-abc-options.html
    """
    from nodejs_wheel import node

    _maybe_build()

    params = {
        **kwargs,
        "scale": scale,
        "staffwidth": staff_width,
    }

    # Run the script
    cmd = [(HERE / "cli.cjs").as_posix()]
    for k, v in params.items():
        cmd.append(f"--{k}={v}")
    cp = node(
        cmd,
        return_completed_process=True,
        input=abc,
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        info = indent(cp.stderr, "| ", lambda _: True)
        raise RuntimeError(f"Failed to render sheet music:\n{info}")

    assert isinstance(cp.stdout, str)

    return cp.stdout


def svg_to(svg: str, fmt: str, **kwargs) -> bytes:
    """Convert an SVG string to another format, returning bytes."""
    try:
        import cairosvg
    except ImportError as e:
        raise RuntimeError(
            "The 'cairosvg' package is required to convert SVG to other formats."
        ) from e

    try:
        func = getattr(cairosvg, f"svg2{fmt.lower()}")
    except AttributeError:
        raise ValueError(
            f"Unsupported format: {fmt!r}. Supported formats include: 'png', 'pdf', 'ps', 'svg'."
        )

    return func(bytestring=svg, **kwargs)


if __name__ == "__main__":
    abc = """\
    K: G
    M: 6/8
    BAG AGE | GED GBd | edB dgb | age dBA |
    """
    # Note: the indent is ignored by abcjs

    svg_str = svg(
        abc,
        scale=3,
        staff_width=800,
        foregroundColor="blue",
        lineThickness=0.2,
    )

    print(svg_str[:500])

    with open(HERE / "test.svg", "w") as f:
        f.write(svg_str)

    for fmt in ["png", "PDF"]:
        with open(f"test.{fmt}", "wb") as f:
            f.write(svg_to(svg_str, fmt))
