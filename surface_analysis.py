import os
import numpy as np

from plot import plot
import analysis

background = np.load(os.path.join("data", "surface_background.npy"))
sample = np.load(os.path.join("data", "surface_sample.npy"))
coordinates = np.load(os.path.join("data", "surface_coordinates.npy"))


x = coordinates[0]
y = coordinates[1]
z = background-sample

#plot(x, y, z, contour=False)
stepsize = x[1] -x[0] #mm
diameter = int(2. / stepsize + 0.5) + 1
sensor = analysis.sensor_function(diameter)
#noise = analysis.detrend2D(x, y, background)
noise = background
zz = analysis.wiener(z, sensor, 0, 1)
#
plot(x, y, zz, contour=False)
