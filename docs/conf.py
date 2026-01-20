import pyabc2

project = "PyABC2"
copyright = "2021\u20132026 zmoon"
author = "zmoon"

version = pyabc2.__version__.split("+")[0]
release = pyabc2.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx.ext.mathjax",
    "myst_nb",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

extlinks = {
    "issue": ("https://github.com/zmoon/PyABC2/issues/%s", "GH%s"),
    "pull": ("https://github.com/zmoon/PyABC2/pull/%s", "PR%s"),
}

exclude_patterns = ["_build"]

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = [
    # TODO: just the pages that need it (example notebooks) instead of every page, using `app.add_js_file`
    (
        "https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js",
        {
            "crossorigin": "anonymous",
            # We need it to load before the widget instances
            # which seem to be in the extensions group (default priority 500)
            "priority": 499,
        },
    )
]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_use_param = True
napoleon_use_rtype = False

autodoc_typehints = "description"
autosummary_generate = True

nb_execution_raise_on_error = True
