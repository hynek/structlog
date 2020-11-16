# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

import codecs
import os
import re


here = os.path.abspath(os.path.dirname(__file__))

# We want an image in the README and include the README in the docs.
suppress_warnings = ["image.nonlocal_uri"]


def read(*parts):
    return codecs.open(os.path.join(here, *parts), "r").read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_toolbox.more_autodoc.autoprotocol",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "structlog"
author = "Hynek Schlawack"
copyright = f"2013, {author}"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = find_version("..", "src", "structlog", "__init__.py")
# The full version, including alpha/beta/rc tags.
release = ""
exclude_patterns = ["_build"]

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = "any"

nitpick_ignore = [
    ("py:class", "BinaryIO"),
    ("py:class", "ILogObserver"),
    ("py:class", "PlainFileObserver"),
    ("py:class", "TLLogger"),
    ("py:class", "TextIO"),
    ("py:class", "structlog._base.BoundLoggerBase"),
    ("py:class", "structlog.dev._Styles"),
]

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"


# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "furo"
html_theme_options = {}
html_logo = "_static/structlog_logo_small_transparent.png"
html_static_path = ["_static"]
htmlhelp_basename = "structlogdoc"

latex_documents = [
    ("index", "structlog.tex", "structlog Documentation", "Author", "manual")
]

# -- Options for manual page output -------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "structlog", "structlog Documentation", ["Author"], 1)]


# -- Options for Texinfo output -----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "structlog",
        "structlog Documentation",
        "Author",
        "structlog",
        "One line description of project.",
        "Miscellaneous",
    )
]


# -- Options for Epub output --------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright


linkcheck_ignore = []

# Twisted's trac tends to be slow
linkcheck_timeout = 300

intersphinx_mapping = {"https://docs.python.org/3": None}
