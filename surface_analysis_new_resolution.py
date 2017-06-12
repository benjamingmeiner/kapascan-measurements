import os
import numpy as np
from plot import plot
from kapascan.sensor import SENSORS
import analysis
import shelve

datadir = "data/background_small_new"
basefilename = "surface"

nr = "002"

with shelve.open(os.path.join(datadir, nr + "_settings")) as file:
    settings= file['settings']

x = np.load(os.path.join(datadir, nr + "_x.npy"))
y = np.load(os.path.join(datadir, nr + "_y.npy"))
z = np.load(os.path.join(datadir, nr + "_z.npy"))
T = np.load(os.path.join(datadir, nr + "_T.npy"))

plot(x, y, T)

# diameter = SENSORS[settings['sensor']]['diameter']
# stepsize = x[1] - x[0]
# diameter_pixel = int(diameter / stepsize + 0.5)
# sensor = analysis.sensor_function(diameter_pixel)
# z_reconstructed = analysis.wiener(z, sensor, noise)
# plot(x, y, z_reconstructed)
