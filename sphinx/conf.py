# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project   = 'Speky'
copyright = '2025'
author    = 'Antoine Gagniere'
release   = os.environ.get('PROJECT_VERSION', '0.0.0')
language  = 'en'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser',
    'sphinx_copybutton',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = []

primary_domain = None

source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme       = 'furo'
#html_static_path = ['_static']
#html_logo        = 'assets/logo.png'

html_theme_options = {
    'navigation_with_keys': True,
}

# -- Myst Parser Options -----------------------------------------------------

myst_fence_as_directive = []
myst_enable_extensions = [
    'attrs_inline', # used to specify the language of an inline code snippet: `void*`{l=C}
    'attrs_block', # used to specify the author of a quote
    'colon_fence', # Allow using ::: instead of ```
]
myst_heading_anchors = 4
myst_words_per_minute = 100
