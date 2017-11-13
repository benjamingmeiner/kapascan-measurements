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


def wiener(y, h, n, s=1, extra=0):
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
        The signal, the power spectral density of the noise is calculated.
        from. If n is a scalar, the value is used as the PSD.

    s : scalar or ndarray (1D or 2D), optional
        The signal, the power spectral density of the origininal signal
        is calculated from. If s is a scalar, the value is used as the
        PSD.

    Returns
    -------
    x : ndarray (1D or 2D)
        An estimate of the original signal.
    """

    def pad(widths):
        return np.array([[width] for width in widths])

    def shape(x):
        return np.array(x.shape)

    # pad signal with edge value to full length of actual convolution
    sensor_widths = np.array([width // 2 for width in h.shape])
    extra_widths = np.array([int(extra * width / 2) for width in h.shape])
    widths = sensor_widths + extra_widths

    y_padded = np.pad(y, pad(widths // 2), mode='linear_ramp')
    y_padded = np.pad(y_padded, pad(widths - widths // 2), mode='constant', constant_values=0)
    y_padded_smoothed = gaussian_filter(y_padded, widths / 8, mode="constant", cval=0)

    zeros_shape = shape(y) - sensor_widths // 2 * 2
    mask = np.zeros(zeros_shape)
    mask = np.pad(mask, pad(sensor_widths // 2), mode='constant', constant_values=1)
    mask = np.pad(mask, pad(widths), mode='constant', constant_values=1)
    mask = gaussian_filter(mask, widths / 8, mode="constant", cval=1)

    y_padded_smoothed_masked = y_padded_smoothed * mask + y_padded * (1 - mask)

    # minimal length for fft to prevent circular convolution
    length = shape(y_padded) + shape(h) - 1

    if not np.isscalar(n):
        N = np.absolute(np.fft.rfftn(n, length))**2
    else:
        N = n
    if not np.isscalar(s):
        S = np.absolute(np.fft.rfftn(s, length))**2
    else:
        S = s

    Y = np.fft.rfftn(y_padded_smoothed_masked, length)
    H = np.fft.rfftn(h, length)
    G = (np.conj(H) * S) / (np.absolute(H)**2 * S + N)
    X = G * Y
    x = np.fft.irfftn(X, length)

    x00 = extra_widths[0]
    x01 = x00 + y.shape[0]
    x10 = extra_widths[1]
    x11 = x10 + y.shape[1]
    return x[x00:x01, x10:x11].copy()


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
