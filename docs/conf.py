# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add service directories to sys.path
sys.path.insert(0, os.path.abspath('../Customer_services'))
sys.path.insert(0, os.path.abspath('../Inventory_service'))
sys.path.insert(0, os.path.abspath('../Reviews_service'))
sys.path.insert(0, os.path.abspath('../Sales'))

# -- Project information -----------------------------------------------------
project = 'Ecommerce Project'
copyright = '2024, Your Name'
author = 'Your Name'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': True,
    'special-members': '__init__',
    'show-inheritance': True,
}

# Napoleon settings for docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# -- Paths for services ------------------------------------------------------
# Ensure each service is correctly imported
sys.path.insert(0, os.path.abspath('../'))
