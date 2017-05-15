import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan'))

from measurement import Measurement
from plot import plot
import numpy as np
import shelve

sensor = '2011'
host = '192.168.254.173'
#serial_port = 'COM3'
serial_port = '/dev/ttyACM0'

settings = {
    'sampling_time': 0.256,
    'data_points': 100,
    'extent': ((1, 1.5, 0.1), (1, 1.5, 0.1)),
    'mode': 'absolute',
    'direction': ('x', 'y'),
    'change_direction': False
    }

m = Measurement(sensor, host, serial_port, settings)
with m:
    #m.interactive_mode()
    x, y, z = m.scan()
    plot(x, y, z)


#datadir = "data"
#filename = "surface"
#for coord, data in zip(("x", "y", "z"), (x, y, z)):
#    np.save(os.path.join(datadir, filename + "_" + coord), data)
#with shelve.open(os.path.join(datadir, filename + "_measurement")) as file:
#    file['measurement'] = m
