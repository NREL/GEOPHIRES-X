import os

import matplotlib as mpl

if os.name == 'nt' and 'TOXPYTHON' in os.environ:
    # Backend should be 'Agg' in GitHub Actions to prevent intermittent Windows failures
    # per https://github.com/NREL/GEOPHIRES-X/issues/365
    mpl.use('Agg')

print(f'[DEBUG] matplotlib backend: {mpl.get_backend()}')
