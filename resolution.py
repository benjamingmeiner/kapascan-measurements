import os
import shelve
import datetime
from subprocess import call
import numpy as np
from kapascan.measurement import Measurement
from kapascan.sendmail import send

host_controller = '192.168.254.173'
host_logger = '192.168.254.51'
serial_port = '/dev/ttyACM0'

resolution = [2, 1, 0.5, 0.2, 0.1, 0.05, 0.02]
settings = {
    'sensors': ['1739'],
    'sampling_time': 0.256,
    'data_points': 50,
    'mode': 'absolute',
    'direction': ('d', ),
    'change_direction': False
    }
email_addr = "b.gmeiner@gmx.de"
base_dir = "data"
measurement_dir = "resolution"

data_dir = os.path.join(base_dir, measurement_dir)
if not os.path.exists(data_dir):
    os.makedirs(data_dir, exist_ok=True)

for i, res in enumerate(resolution):
    settings['extent'] = ((15.5, 21.5, res), (8.0, 14, res))

    email_subject = "'{}': Measurement {}".format(measurement_dir, res)
    email_body = "Started at {}".format(datetime.datetime.now())
    m = Measurement(host_controller, serial_port, host_logger, settings)
    send(email_addr, email_subject, email_body)
    with m:
        x, y, z, T = m.scan()

    filename = "{:03d}".format(i)
    for coord, data in zip(("x", "y", "z", "T"), (x, y, z, T)):
        np.save(os.path.join(data_dir, filename + "_" + coord), data)
    with shelve.open(os.path.join(data_dir, filename + "_settings")) as file:
        file['settings'] = m.settings

    call("git add {}".format(data_dir), shell=True)
    call('git commit -m "Data: Measurement {}."'.format(i), shell=True)
    call("git push", shell=True)

    email_body = "Finished at {}".format(datetime.datetime.now())
    send(email_addr, email_subject, email_body)

