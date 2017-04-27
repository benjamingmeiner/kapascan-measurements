import os
import numpy as np
from plot import plot
import matplotlib.pyplot as plt
import analysis

datadir = "data"

background = np.load(os.path.join(datadir, "surface_background.npy"))
background2 = np.load(os.path.join(datadir, "surface_background2.npy"))
sample = np.load(os.path.join(datadir, "surface_sample.npy"))

x = np.load(os.path.join(datadir, "surface_x.npy"))
y = np.load(os.path.join(datadir, "surface_y.npy"))
z = 0.5 * background + 0.5 * background2 - sample

noise = (background2 - background) * 0.00005
noise -= noise.mean()

stepsize = x[1] - x[0]
diameter = int(8.2 / stepsize + 0.5)
sensor = analysis.sensor_function(diameter)
z_reconstructed = analysis.wiener(z, sensor, noise)

line = ((4, 4), (20.95, 17.95))
fig = plot(x, y, z_reconstructed)
