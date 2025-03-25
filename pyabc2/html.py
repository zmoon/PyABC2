"""Generate an HTML page to render ABC with abcjs."""

FULLPAGE_TPL = """\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>{title:s}</title>
    <script src="https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js"></script>
    <style>
      div#notation {{
        white-space: pre-wrap;
        font-family: monospace;
      }}
    </style>
  </head>
  <body>
    <div id="notation">
{abc:s}
    </div>
    <script>
      const target = document.getElementById("notation");
      const abc = target.textContent;
      const params = {params:s};
      ABCJS.renderAbc(target, abc, params);
    </script>
  </body>
</html>
"""


def html(
    abc: str,
    *,
    #
    title: str = "abc",
    # Keep names consistent with the widget!
    scale: float = 1.0,
    staff_width: int = 740,
    **kwargs,
):
    """Generate an HTML page to render ABC with abcjs, returning string.

    Parameters
    ----------
    abc
        The ABC notation to render.
    **kwargs
        Additional abcjs options that haven't been explicitly defined here
        in the signature.
        https://paulrosen.github.io/abcjs/visual/render-abc-options.html
    """
    params = {
        **kwargs,
        "scale": scale,
        "staffwidth": staff_width,
    }

    ind = 6
    abc_indented = "\n".join(" " * ind + line.lstrip() for line in abc.strip().splitlines())

    ind = 6
    s_param_lines = "\n".join(" " * (ind + 2) + f"{k}: {v!r}," for k, v in sorted(params.items()))
    s_params = r"{" + "\n" + s_param_lines + "\n" + " " * ind + "}"

    s = FULLPAGE_TPL.format(
        title=title,
        abc=abc_indented,
        params=s_params,
    )

    return s


def open_html(
    *args,
    **kwargs,
) -> None:
    """Generate an HTML page to render ABC with abcjs
    and open it in a new tab with the default web browser."""
    from tempfile import NamedTemporaryFile
    from webbrowser import open_new_tab

    s = html(*args, **kwargs)
    with NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(s)
        path = f.name

    open_new_tab(path)


if __name__ == "__main__":  # pragma: no cover
    abc = """\
    T: Awesome Tune
    K: G
    M: 6/8
    BAG AGE | GED GBd | edB dgb | age dBA |
    """
    # Note: the indent is ignored by abcjs

    open_html(abc, title="abcjs!", scale=3, foregroundColor="forestgreen")
