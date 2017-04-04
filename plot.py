import matplotlib.pyplot as plt
import numpy as np


def plot(x, y, z, contour=True):
    xis1D = True if x.shape[0] is 1 else False
    yis1D = True if y.shape[0] is 1 else False
    if xis1D and yis1D:
        pass
    elif xis1D and not yis1D:
        plot1D(y, np.transpose(z)[0], "$y$ [mm]", "z [µm]")
    elif yis1D and not xis1D:
        plot1D(x, z[0], "$x$ [mm]", "$z$ [µm]")
    else:
        plot2D(x, y, z)


def plot1D(x, y, xlabel, ylabel): 
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def extent(x, y):
    """
    Calculates extent values to be used by imshow()

    Parameters
    ----------
    x, y : 1D-arrays
        The vectors spanning the measurment area

    Returns
    -------
    extent : tuple
        The extent values
    """
    dx = (x[-1] - x[0]) / (2 * len(x))
    dy = (y[-1] - y[0]) / (2 * len(y))
    
    if dx == 0 and dy == 0:
        dx, dy = 1, 1
    else:
        if dx == 0:
            dx = dy
        if dy == 0:
            dy = dx
    return (x[0] - dx, x[-1] + dx, y[0] - dy, y[-1] + dy)


def plot2D(x, y, z, contour=False): 
    ext = extent(x, y)
    fig, ax = plt.subplots()
    if contour:
        ax.contour(z, colors='k', extent=ext, linewidths=0.5)
    cax = ax.imshow(z, origin='lower', extent=ext, aspect='equal')
    cbar = fig.colorbar(cax)
    tick_step = [int(np.ceil(len(c) / 11)) for c in [x, y]]
    ax.set_xticks(x[::tick_step[0]])
    ax.set_yticks(y[::tick_step[1]])
    cbar.set_ticks(np.linspace(z.min(), z.max(), 8))
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    cbar.set_label("z [µm]")
