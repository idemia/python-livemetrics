
import livemetrics

project = 'livemetrics'
copyright = livemetrics.__copyright__
version = livemetrics.__version__
release = livemetrics.__version__

master_doc = 'index'

html_static_path = ['_static']
html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'idemia',
    'github_repo': 'python-livemetrics',
    'github_button': True,
    'show_relbars': True,
    'fixed_sidebar': False,
}
extensions = ['sphinx.ext.autodoc']
