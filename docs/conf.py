import sphinx_py3doc_enhanced_theme

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.ifconfig',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'm2r2',
]
source_suffix = ['.rst', '.md']
master_doc = 'index'
project = 'geophires-x'
year = '2023'
author = 'NREL'
copyright = f'{year}, {author}'
version = release = '3.4.21'

pygments_style = 'trac'
templates_path = ['./templates']
extlinks = {
    'issue': ('https://github.com/NREL/python-geophires-x/issues/%s', '#'),
    'pr': ('https://github.com/NREL/python-geophires-x/pull/%s', 'PR #'),
}

# html_theme = 'alabaster' # alternative possible theme

html_theme = 'sphinx_py3doc_enhanced_theme'
html_theme_path = [sphinx_py3doc_enhanced_theme.get_html_theme_path()]
html_theme_options = {
    'githuburl': 'https://github.com/NREL/python-geophires-x/',
}

html_use_smartypants = True
html_last_updated_fmt = '%b %d, %Y'
html_split_index = False
html_sidebars = {
    '**': ['searchbox.html', 'globaltoc.html', 'sourcelink.html'],
}
html_short_title = f'{project}-{version}'

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
