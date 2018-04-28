import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from skimage.measure import profile_line
import numpy as np
import datetime
from matplotlib.dates import HourLocator, DateFormatter

from mpl_toolkits.axes_grid1.inset_locator import inset_axes, zoomed_inset_axes
#from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar


def _extent(x, y):
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
    dx = 0.5 * (x[-1] - x[0]) / (len(x) - 1)
    dy = 0.5 * (y[-1] - y[0]) / (len(y) - 1)
    
    if dx == 0 and dy == 0:
        dx, dy = 1, 1
    else:
        if dx == 0:
            dx = dy
        if dy == 0:
            dy = dx
    return (x[0] - dx, x[-1] + dx, y[0] - dy, y[-1] + dy)


def plot(x, y, z, what="z", title="", contour=False, limits=None, psf=None, psf_loc=3):
    x = np.asarray(x)
    y = np.asarray(y)
    z = np.asarray(z)
    ext = _extent(x, y)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    if limits is None:
        limits = (z.min(), z.max())
    if contour:
        ax.contour(z, colors='k', extent=ext, linewidths=0.5)
    image = ax.imshow(z, origin='lower', extent=ext, aspect='equal', 
                      vmin=limits[0], vmax=limits[1], picker=True)
    if psf is not None:
        width = "{}%".format(psf.shape[0] / len(x) * 100)
        height = "{}%".format(psf.shape[1] / len(y) * 100)
        inset_ax = inset_axes(ax, height=height, width=width, loc=psf_loc)
        inset_ax.imshow(psf)
        inset_ax.get_xaxis().set_visible(False)
        inset_ax.get_yaxis().set_visible(False)
    cbar = fig.colorbar(image)
    tick_step = [int(np.ceil(len(c) / 11)) for c in [x, y]]
    ax.set_xticks(x[::tick_step[0]])
    ax.set_yticks(y[::tick_step[1]])
    cbar.set_ticks(np.linspace(*limits, 8))
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_title(title, y=1.05)
    if what.lower() in ["z", "surface"]:
        cbar.set_label("z [µm]")
    elif what.lower() in ["t", "temp", "temperature"]:
        cbar.set_label("Temperature [°C]"), 
    return fig, ax


def plot_profile(x, y, z, src, dst, title="Profile Line"):
    x = np.asarray(x)
    y = np.asarray(y)
    z = np.asarray(z)
    if len(z.shape) == 2:
        z = [z]
    xextent = x[-1] - x[0]
    yextent = y[-1] - y[0]
    src_pixel = [0, 0]
    dst_pixel = [0, 0]
    src_pixel[0] = len(y) * (src[1] - y[0]) / yextent
    src_pixel[1] = len(x) * (src[0] - x[0]) / xextent
    dst_pixel[0] = len(y) * (dst[1] - y[0]) / yextent
    dst_pixel[1] = len(x) * (dst[0] - x[0]) / xextent
    
    z_profiles = []
    for zi in z:
        z_profiles.append(profile_line(zi, src_pixel, dst_pixel, linewidth=1, order=1, mode='nearest'))

    fig, ax1 = plt.subplots(figsize=(8, 7))
    x_profile = np.linspace(src[0], dst[0], len(z_profiles[0]))
    for z_profile in z_profiles:
        ax1.plot(x_profile, z_profile)
        
    ax2 = ax1.twiny()
    lim1 = list(sorted([src[0], dst[0]]))
    lim2 = list(sorted([src[1], dst[1]]))
    ax1.set_xlim(lim1)
    ax2.set_xlim(lim2)
    
    ax1.set_xticks(np.linspace(ax1.get_xbound()[0], ax1.get_xbound()[1], 8))
    ax2.set_xticks(np.linspace(ax2.get_xbound()[0], ax2.get_xbound()[1], 8))
    ax1.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax2.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax1.set_xlabel("$x$ [mm]")
    ax2.set_xlabel("$y$ [mm]")
    ax1.set_ylabel("$z$ [µm]")
    ax1.set_title(title, y=1.1)
    ax1.grid()
    return fig, (ax1, ax2)


class ProfileBuilder():
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax
        self.coords = []
        self.connect()
    
    def connect(self):
        self.id_press = self.fig.canvas.mpl_connect(
            'button_press_event', self.on_click)

    def clear_image(self):
        self.coords = []
        while(self.ax.lines):
            self.ax.lines.pop()
        plt.show()        
        
    def on_click(self, event):
        if event.button == 1:
            if len(self.coords) == 2:
                self.clear_image()
            self.coords.append((event.xdata, event.ydata))
        else:
            self.clear_image()
        if len(self.coords) == 2:
            x = [self.coords[0][0], self.coords[1][0]]
            y = [self.coords[0][1], self.coords[1][1]]
            self.ax.plot(x, y, color=(0.7, 0.1, 0))


def cat1d(x):
    x_flat = [xi.flatten() for xi in x]
    return np.concatenate(x_flat)


def logscale(x, a=1):
    return np.log(x - x.min() + 1) ** (1/a)


def plot_temp_trend(t, T):
    dt = np.array([[datetime.datetime.fromtimestamp(tii) for tii in ti] for ti in t])
    fig, ax = plt.subplots()
    ax.plot(cat1d(dt), cat1d(T))
    ax.xaxis.set_major_locator(HourLocator())
    ax.xaxis.set_major_formatter(DateFormatter("%H:%M"))
    fig.autofmt_xdate()
    return fig, ax


def plot_raw(data, times):
    fig, ax = plt.subplots()
    nr_of_samples = data.shape[1]
    t = np.linspace(*times, nr_of_samples)
    for d in data:
        ax.plot(t, d)
    ax.set_xlabel("t [s]")
    ax.set_ylabel("z [µm]")
    return fig, ax