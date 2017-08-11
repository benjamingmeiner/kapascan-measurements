import os
import shelve
import datetime
import glob
from subprocess import run, PIPE
import numpy as np
from kapascan.measurement import Measurement, MeasurementError
from . import plot


host_controller = '192.168.254.173'
host_logger = '192.168.254.174'
serial_port = '/dev/ttyACM0'

base_dir = "data"
script_dir = os.path.dirname(os.path.realpath(__file__))


def _make_prefix(data_dir, i):
    while True:
        prefix = os.path.join(data_dir, "{:03d}_".format(i))
        if glob.glob(prefix + "*"):
            i += 1
        else:
            return prefix


def measure(settings, directory, script_filename, repeat=1, wipe_after=None):
    data_dir = os.path.join(base_dir, directory)
    os.makedirs(data_dir, exist_ok=True)
    m = Measurement(host_controller, serial_port, host_logger, settings)
    if wipe_after is not None and wipe_after >= 0:
        m.check_wipe()
    for i in range(1, repeat + 1):
        with m:
            if wipe_after is not None and i == wipe_after + 1:
                m.wipe()
            x, y, z, T, t = m.scan()
        prefix = _make_prefix(data_dir, i)
        print(prefix)
        for coord, data in zip(("x", "y", "z", "T", "t"), (x, y, z, T, t)):
            np.save(prefix + coord, data)
        with shelve.open(prefix + "settings") as file:
            file['settings'] = m.settings
        commit_message = "Measurement {} in {}.".format(i, directory)
        response = run([os.path.join(script_dir, "git.sh"),
                        data_dir, script_filename, commit_message],
                       stdout=PIPE, stderr=PIPE)
        if response.returncode != 0:
            print(response.stdout.decode('utf-8'))
            raise Exception(response.stderr.decode('utf-8'))
    return m


def align(settings, check_wipe=False):
    with Measurement(host_controller, serial_port, host_logger, settings) as m:
        if check_wipe:
            try:
                m.check_wipe()
            except MeasurementError as error:
                print(error)
            else:
                print("Wiping possible.")
        x, y, z, T, t =  m.scan()
        plot.plot(x, y, z[0])
        return x, y, z, T, t

