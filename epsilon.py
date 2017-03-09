# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 15:18:49 2017

@author: nabilah
"""
import helper
import controller
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
import importlib
importlib.reload(controller)

host = '192.168.254.173'
data_points = 10000
sampling_time = 0.1  # ms
c = controller.Controller(2000, host)

dm = []
d2 = []

#TODO implement repeat measurement
while helper.query_yes_no("Start next measurement?"):
    d2.append(float(input("Enter measured thickness [mm]: ")))
    data = c.acquire(data_points, sampling_time, channels=[0]) / 1000
    x = np.arange(len(data))
    slope, intercept  = scipy.stats.linregress(x, data)[0:2]
    dm.append(intercept)
    g = slope * x + intercept
    plt.plot(x, data, x, g)
    plt.show()

np.save("data\\epsilon_dm.npy", dm)
np.save("data\\epsilon_d2.npy", d2)