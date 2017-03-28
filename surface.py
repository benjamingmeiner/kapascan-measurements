import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan'))

from measurement import Measurement
import numpy as np
import matplotlib.pyplot as plt

with Measurement() as m:
    x, y, z = m.measure(20, 20, 21, 21, 0.2)

dx = (x[-1] - x[0]) / (2 * len(x))
dy = (y[-1] - y[0]) / (2 * len(y))
extent = (x[0] - dx, x[-1] + dx, y[0] - dy, y[-1] + dy)

fig, ax = plt.subplots()
ax.contour(z, colors='k', extent=extent, linewidths=0.5)
cax = ax.imshow(z, origin='lower', extent=extent, aspect='equal')
cbar = fig.colorbar(cax)
ax.set_xticks(x)
ax.set_yticks(y)
cbar.set_ticks(np.linspace(z.min(), z.max(), 8))
ax.set_xlabel("x [mm]")
ax.set_ylabel("y [mm]")
cbar.set_label("z [µm]")