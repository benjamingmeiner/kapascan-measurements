import os
import numpy as np
from kapascan.plot import plot
from kapascan.sensor import SENSORS
import analysis
import shelve

datadir = "data/background"
for filename in ["{:03d}".format(i) for i in range(2,8)]:

    with shelve.open(os.path.join(datadir, filename + "_settings")) as file:
        settings= file['settings']

        z = np.load(os.path.join(datadir, filename + "_z.npy"))
        T = np.load(os.path.join(datadir, filename + "_T.npy"))
        x = np.load(os.path.join(datadir, filename + "_x.npy"))
        y = np.load(os.path.join(datadir, filename + "_y.npy"))

        plot(x, y, T)
