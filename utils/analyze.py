import os
import shelve
import numpy as np
import lmfit
from skimage import draw
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.interpolation import rotate
import cairocffi as cairo
import matplotlib.pyplot as plt
from .measure import _make_prefix


base_dir = "data"


def load_data(directory, numbers):
    x, y, z, T, t, settings = [[] for _ in range(6)]
    data_dir = os.path.join(base_dir, directory)
    filename_template = "%03d_%s.npy"
    for i in numbers:
        x.append(np.load(os.path.join(data_dir, filename_template % (i, "x"))))
        y.append(np.load(os.path.join(data_dir, filename_template % (i, "y"))))
        z.append(np.load(os.path.join(data_dir, filename_template % (i, "z"))))
        T.append(np.load(os.path.join(data_dir, filename_template % (i, "T"))))
        t.append(np.load(os.path.join(data_dir, filename_template % (i, "t"))))
        with shelve.open(os.path.join(data_dir, '%03d_settings' % i)) as file:
            settings.append(file['settings'])
    return x, y, z, T, t, settings


def load_raw_data(directory, numbers):
    data, time, settings = [[] for _ in range(3)]
    data_dir = os.path.join(base_dir, directory)
    filename_template = "%03d_%s.npy"
    for i in numbers:
        data.append(np.load(os.path.join(data_dir, filename_template % (i, "data"))))
        time.append(np.load(os.path.join(data_dir, filename_template % (i, "time"))))
        with shelve.open(os.path.join(data_dir, '%03d_settings' % i)) as file:
            settings.append(file['settings'])
    return data, time, settings


def wiener(y, h, n, s=1):
    """
    2D Wiener deconvolution. Implemented as defined in
    https://en.wikipedia.org/wiki/Wiener_deconvolution

    Parameters
    ----------
    y : ndarray (1D or 2D)
        The observed signal

    h : ndarray (1D or 2D)
        The impulse response (point spread function) of the system

    n : scalar or ndarray (1D or 2D)
        The signal from which the power spectral density of the noise is
        calculated. If n is a scalar the value is used directly as the PSD.

    s : scalar or ndarray (1D or 2D), optional
        The signal from which the power spectral density of the origininal
        signal is calculated. If s is a scalar the value is used directly as
        the PSD.

    Returns
    -------
    x : ndarray (1D or 2D)
        An estimate of the original signal.
    """

    # pad signal with zeros to full length of actual convolution
    widths = [[width // 2] for width in h.shape]
    y_padded = np.pad(y, widths, mode='edge')
    # minimal length for fft to prevent circular convolution
    length = [sy + sh - 1  for sy, sh in zip(y_padded.shape, h.shape)]

    if not np.isscalar(n):
        N = np.absolute(np.fft.rfftn(n, length))**2
    else:
        N = n
    if not np.isscalar(s):
        S = np.absolute(np.fft.rfftn(s, length))**2
    else:
        S = s

    Y = np.fft.rfftn(y_padded, length)
    H = np.fft.rfftn(h, length)
    G = (np.conj(H) * S) / (np.absolute(H)**2 * S + N)
    X = G * Y
    x = np.fft.irfftn(X, length)

    if len(y.shape) == 1:
        return x[:y.shape[0]].copy()
    if len(y.shape) == 2:
        return x[:y.shape[0],:y.shape[1]].copy()


def sensor_function(diameter, sigma=0):
    """
    Generates a 2D devonvolution kernel with a circular shape.

    Parameters
    ----------
    diameter : float
        diameter of the sensor in pixels
    sigma : float, optional
        width of the gaussian filter in pixels

    Returns
    -------
    kernel : 2D array
        The deconvolution kernel
    """
    dim = int(np.ceil(diameter))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, dim, dim)
    contex = cairo.Context(surface)

    radius = diameter / 2
    center = dim / 2
    contex.arc(center, center, radius, 0, 2 * np.pi)
    contex.fill()
    kernel = np.frombuffer(surface.get_data(), dtype=np.uint32).astype(np.float)
    kernel = kernel.reshape(dim, dim)
    
    # smooth boarder
    kernel = np.pad(kernel, int(np.ceil(4*sigma)), 'constant')
    kernel = gaussian_filter(kernel, sigma, mode='constant')
    kernel /= kernel.sum()
    return kernel


def sample_shape(coords, x, y, height=1, structure_height=0, structure_k=(1, 1), structure_angle=0, sigma=0):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, len(x), len(y))
    contex = cairo.Context(surface)
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    
    def rel(vx, vy):
        return ((vx - x[0]) / dx, (vy - y[0]) / dy)
    
    contex.move_to(*rel(*coords[0]))
    for cx, cy in coords:
        contex.line_to(*rel(cx, cy))
    contex.fill()
    img = np.frombuffer(surface.get_data(), dtype=np.uint32).astype(np.float)
    img *= height / img.max()
    img = img.reshape(len(y), len(x))
    
    xx, yy = np.meshgrid(range(len(x)), range(len(y)))
    structure = 0.5 * structure_height * (np.sin(2 * np.pi / structure_k[0] * xx) +
                                    np.cos(2 * np.pi / structure_k[1] * yy))
    structure = rotate(structure, structure_angle, reshape=False, mode='reflect')
    nonzero = np.where(np.abs(img) > np.abs(0.99 * height))
    img[nonzero] += structure[nonzero]
    
    img = gaussian_filter(img, sigma, mode='constant')
    return img


def residual(params, data):
    a = params['a']
    b = params['b']
    c = params['c']

    leny, lenx = data.shape
    xx, yy = np.meshgrid(np.arange(lenx), np.arange(leny))
    model = a * xx + b * yy + c
    return (data - model)


def detrend2D(z):
    params = lmfit.Parameters()
    params.add('a', value=0)
    params.add('b', value=0)
    params.add('c', value=0)

    result = lmfit.minimize(residual, params, args=(z,))
    return residual(result.params, z)
