import numpy as np
import lmfit
from skimage import draw

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
    y_padded = np.pad(y, widths, mode='constant', constant_values=0)
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


def sensor_function(diameter, dim=2):
    """
    Generates a 1D / 2D devonvolution kernel with the size of the sensor.

    Parameters
    ----------
    diameter : int
        diameter of the sensor
    dim : int, optional
        dimensionality of the output. Defaults to 2.

    Returns
    -------
    kernel : 1D / 2D array
        The deconvolution kernel
    """
    radius = diameter // 2
    if dim == 1:
        kernel = np.ones(diameter)
    elif dim == 2:
        kernel = np.zeros((diameter, diameter))
        r, c, val = draw.circle_perimeter_aa(radius, radius, radius)
        kernel[r, c] = val
        r, c, = draw.circle(radius, radius, radius)
        kernel[r, c] = 1
    kernel /= kernel.sum()
    return kernel


def residual(params, x, y, data):
    a = params['a']
    b = params['b']
    c = params['c']

    xx, yy = np.meshgrid(x, y)
    model = a * xx + b * yy + c
    return (data - model)

def detrend2D(x, y, z):
    params = lmfit.Parameters()
    params.add('a', value=0)
    params.add('b', value=0)
    params.add('c', value=0)
    params.add('d', value=0)
    params.add('e', value=1000)

    result = lmfit.minimize(residual, params, args=(x, y, z))
    print(result.params)
    return residual(result.params, x, y, z)

