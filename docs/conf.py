import pyabc2

project = "PyABC2"
copyright = "2021\u20132025 zmoon"
author = "zmoon"

version = pyabc2.__version__.split("+")[0]
release = pyabc2.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "myst_nb",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

exclude_patterns = ["_build"]

html_theme = "furo"

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True
napoleon_use_param = True
napoleon_use_rtype = False

autodoc_typehints = "description"
autosummary_generate = True

nb_execution_raise_on_error = True
