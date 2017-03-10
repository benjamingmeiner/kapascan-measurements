import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan'))

import helper
import controller
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt


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

np.save(os.path.join("data", "epsilon_dm.npy"), dm)
np.save(os.path.join("data", "epsilon_d2.npy"), d2)

