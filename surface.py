import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan'))

from measurement import Measurement

host = '192.168.254.173'
serial_port = 'COM3'
settings = {
        'sampling_time': 0.05,
        'data_points': 10,
        'x_range': (1, 2, 0.1),
        'y_range': (3, 4, 0.1)
        }

with Measurement(host, serial_port, **settings) as m:
    coordinates, extent, data = m.scan()
