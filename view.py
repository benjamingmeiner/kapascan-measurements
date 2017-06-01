import os
import numpy as np
from kapascan.plot import plot
from kapascan.sensor import SENSORS
import analysis
import shelve

datadir = "data/background"

z = []
T = []
x = []
y = []
for filename in ["{:03d}".format(i) for i in range(2,8)]:
    with shelve.open(os.path.join(datadir, filename + "_settings")) as file:
        settings= file['settings']

        z.append(np.load(os.path.join(datadir, filename + "_z.npy")))
        T.append(np.load(os.path.join(datadir, filename + "_T.npy")))
        x.append(np.load(os.path.join(datadir, filename + "_x.npy")))
        y.append(np.load(os.path.join(datadir, filename + "_y.npy")))

for i in range(len(z)-1):
    plot(x[i], y[i], T[i])

