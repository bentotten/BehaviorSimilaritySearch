# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path

sys.path.insert(0, str(Path("../packages/behavior_core/src").resolve()))
sys.path.insert(0, str(Path("../apps/behavior_cli/src").resolve()))

# -- Project information -----------------------------------------------------

project = "BehaviorSimilaritySearch"
author = "BehaviorSimilaritySearch Contributors"
release = "0.1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",       # Pull docstrings from source
    "sphinx.ext.napoleon",      # Support Google-style docstrings
    "sphinx.ext.viewcode",      # Add links to source code
    "sphinx.ext.intersphinx",   # Link to external docs (e.g. Python stdlib)
    "sphinx_autodoc_typehints", # Render type hints in docs
]

# Google-style docstrings via napoleon
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# autodoc settings
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# intersphinx mappings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build"]

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
