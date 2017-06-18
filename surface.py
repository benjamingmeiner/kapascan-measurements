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

settings = {
    'sensors': ['1739'],
    'sampling_time': 0.256,
    'data_points': 50,
    'extent': ((19.5, 24.5, 0.015), (5, 9.5, 0.015)),
    'mode': 'absolute',
    'direction': ('x', 'y'),
    'change_direction': False
    }

email_addr = "b.gmeiner@gmx.de"

for i in range(21, 50):

    email_subject = "Measurement {}".format(i)
    email_body = "Started at {}".format(datetime.datetime.now())
    m = Measurement(host_controller, serial_port, host_logger, settings)
    send(email_addr, email_subject, email_body)
    with m:
        x, y, z, T = m.scan()

    datadir = "data/small"
    filename = "{:03d}".format(i)
    for coord, data in zip(("x", "y", "z", "T"), (x, y, z, T)):
        np.save(os.path.join(datadir, filename + "_" + coord), data)
    with shelve.open(os.path.join(datadir, filename + "_settings")) as file:
        file['settings'] = m.settings

    call("git add {}".format(datadir))
    call('git commit -m "Data: Measurement {}."'.format(i))
    call("git push")

    email_body = "Finished at {}".format(datetime.datetime.now())
    send(email_addr, email_subject, email_body)
