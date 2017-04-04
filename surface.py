import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan'))

from measurement import Measurement
import plot

host = '192.168.254.173'
serial_port = 'COM3'
settings = {
        'sampling_time': 0.05,
        'data_points': 100,
        'extent': ((1, 18, 0.1), (1, 18, 0.1))
        }

with Measurement(host, serial_port, **settings) as m:
    m.interactive_mode()
    #x, y, z = m.scan()
    #plot.plot(x, y, z)
