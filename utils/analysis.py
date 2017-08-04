import numpy as np
import lmfit
from skimage import draw
from scipy.ndimage.filters import gaussian_filter
import cairocffi as cairo

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
