import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter


signal = np.ones(171)
noise = np.random.normal(0, 0.05, signal.shape)
y = signal + noise

extra = 5
y_width = len(signal)
sensor_width = 30
extra_width = int(extra * sensor_width / 2)
width = sensor_width + extra_width

y_padded = np.pad(y, width // 2, mode='linear_ramp')
y_padded = np.pad(y_padded, width - width // 2, mode='constant')

y_padded_smoothed_full = gaussian_filter(y_padded, width / 8, mode="constant", cval=0)

zeros_shape = len(y) - sensor_width // 2 * 2
mask = np.zeros(zeros_shape)
mask = np.pad(mask, sensor_width // 2, mode='constant', constant_values=1)
mask = np.pad(mask, width, mode='constant', constant_values=1)
mask = gaussian_filter(mask, sensor_width / 8, mode="constant", cval=1)

y_padded_smoothed = y_padded_smoothed_full * mask + y_padded * (1 - mask)


plt.figure()
plt.plot(y_padded)
plt.plot(y_padded_smoothed)
plt.plot(mask)
#plt.plot(y_padded_smoothed)
