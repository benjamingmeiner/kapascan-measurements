import os
from kapascan.measurement import Measurement
from kapascan.plot import plot
import numpy as np
import shelve

host_controller = '192.168.254.173'
host_logger = '192.168.254.51'
#serial_port = 'COM3'
serial_port = '/dev/ttyACM0'

settings = {
    'sensor': '2011',
    'sampling_time': 0.256,
    'data_points': 100,
    'extent': ((1, 15, 0.1), (1, 15, 0.1)),
    'mode': 'absolute',
    'direction': ('x', 'y'),
    'change_direction': False
    }

for i in range(999):
    m = Measurement(host_controller, serial_port, host_logger, settings)
    with m:
        # m.interactive_mode()
        x, y, z, T = m.scan()
        #plot(x, y, z)
        #plot(x, y, T)


    datadir = "data/background"
    filename = "{:03d}".format(i)
    for coord, data in zip(("x", "y", "z", "T"), (x, y, z, T)):
        np.save(os.path.join(datadir, filename + "_" + coord), data)
    with shelve.open(os.path.join(datadir, filename + "_settings")) as file:
        file['settings'] = m.settings
