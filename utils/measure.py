import os
import shelve
import datetime
import glob
import logging
import time
from subprocess import run, PIPE
import numpy as np
from kapascan.measurement import Measurement, MeasurementError
from kapascan.controller import Controller, ControllerError
from kapascan.table import Table
from kapascan.helper import BraceMessage as __
from . import plot
from .log import log_exception
from .analyze import _make_prefix

host_controller = '192.168.254.173'
host_logger = '192.168.254.174'
serial_port = '/dev/ttyACM0'

base_dir = "data"
script_dir = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger(__name__)


@log_exception
def measure(settings, directory, script_filename, repeat=1, wipe_after=None):
    logger.info(__("Measurement {}:", directory))
    data_dir = os.path.join(base_dir, directory)
    os.makedirs(data_dir, exist_ok=True)
    m = Measurement(host_controller, serial_port, host_logger, settings)
    if wipe_after is not None and wipe_after >= 0:
        m.check_wipe()
    for i in range(1, repeat + 1):
        logger.info(__("Scan {} of {}:", i, repeat))
        with m:
            if wipe_after is not None and i == wipe_after + 1:
                m.wipe()
            try:
                x, y, z, T, t = m.scan()
            except MeasurementError as error:
                print(error)
                return
        prefix = _make_prefix(data_dir, i)
        for coord, data in zip(("x", "y", "z", "T", "t"), (x, y, z, T, t)):
            np.save(prefix + coord, data)
        with shelve.open(prefix + "settings") as file:
            file['settings'] = m.settings
        logger.info(__("Written measurement data to {}.", prefix))
        commit_message = "Measurement {}: Data {}.".format(directory, i)
        response = run([os.path.join(script_dir, "git.sh"),
                        data_dir, script_filename, commit_message],
                       stdout=PIPE, stderr=PIPE)
        logger.info(__("Switched to branch {} and commited data.", directory))
        if response.returncode != 0:
            raise Exception(response.stderr.decode('utf-8'))
    return m


@log_exception
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
        for zi in z:
            plot.plot(x, y, zi)
        return x, y, z, T, t


@log_exception
def align_raw(settings):
    c = Controller(settings['sensors'], host_controller)
    with c:
        t0 = time.time()
        data = c.acquire(settings['data_points'], settings['mode'], settings['sampling_time'])
        t1 = time.time()
    plot.plot_raw(data, [0, t1 - t0])
    return data, [t0, t1]


@log_exception
def move():
    with Table(serial_port) as t:
        t.interact()


@log_exception
def save_raw(data, times, settings, directory, script_filename, i):
    data_dir = os.path.join(base_dir, directory)
    os.makedirs(data_dir, exist_ok=True)
    prefix = _make_prefix(data_dir, i)
    np.save(prefix + "data", data)
    np.save(prefix + "time", times)
    with shelve.open(prefix + "settings") as file:
        file['settings'] = settings
    logger.info(__("Written raw measurement data to {}.", prefix))
    commit_message = "Raw Measurement {} in {}.".format(prefix[-4:-1], directory)
    response = run([os.path.join(script_dir, "git.sh"),
                    data_dir, script_filename, commit_message],
                   stdout=PIPE, stderr=PIPE)
    logger.info(__("Switched to branch {} and commited data.", directory))
    if response.returncode != 0:
        raise Exception(response.stderr.decode('utf-8'))


@log_exception
def raw_measure(settings, directory, script_filename, repeat=1):
    logger.info(__("Raw Measurement {}.", directory))
    logger.info(__("Acquiring data with settings:\n", settings, pretty=True))

    c = Controller(settings['sensors'], host_controller)
    for i in range(1, repeat + 1):
        logger.info(__("Acquisition {} of {}:", i, repeat))
        with c:
            try:
                t0 = time.time()
                data = c.acquire(settings['data_points'], settings['mode'], settings['sampling_time'])
                t1 = time.time()
            except ControllerError as error:
                print(error)
                return
    return c