import matplotlib

# Backend should be 'Agg' in GitHub Actions to prevent intermittent Windows failures
# per https://github.com/NREL/GEOPHIRES-X/issues/365
print(f'[DEBUG] matplotlib backend: {matplotlib.get_backend()}')
