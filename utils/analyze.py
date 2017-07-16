import os
from .measure import _make_prefix
import matplotlib.pyplot as plt
import numpy as np
import shelve

base_dir = "data"

def load_data(directory, numbers):
    x, y, z, T, settings = [[] for _ in range(5)]
    data_dir = os.path.join(base_dir, directory)
    filename_template = "%03d_%s.npy"
    for i in numbers:
        x.append(np.load(os.path.join(data_dir, filename_template % (i, "x"))))
        y.append(np.load(os.path.join(data_dir, filename_template % (i, "y"))))
        z.append(np.load(os.path.join(data_dir, filename_template % (i, "z"))))
        T.append(np.load(os.path.join(data_dir, filename_template % (i, "T"))))
        with shelve.open(os.path.join(data_dir, '%03d_settings' % i)) as file:
            settings.append(file['settings'])
    return x, y, z, T
