import numpy as np

# Define the alias once at module level.
# NumPy 2.0+ uses 'trapezoid', older versions use 'trapz'.
if hasattr(np, 'trapezoid'):
    np_trapz = np.trapezoid
else:
    np_trapz = np.trapz
