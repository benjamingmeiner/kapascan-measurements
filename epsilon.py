from kapascan.helper import query_options
from kapascan.controller import Controller
import scipy.stats
import numpy as np
import matplotlib.pyplot as plt
#%matplotlib inline

sensor = '2011'
host = '192.168.254.173'

data_points = 2000
sampling_time = 0.256  # ms
c = Controller(sensor, host)

dm = []
d2 = []

with c:
    c.set_sampling_time(sampling_time)
    c.set_trigger_mode('continuous')
    while True:
        print()
        print("Continue?")
        choice = query_options(["Next", "Repeat", "Stop"], 1)
        if choice == 3:
            break
        if choice == 1:
            print()
            print("Enter measured thickness [mm]")
            print("(starts measurement)")
            while True:
                response = input("--->  ")
                try:
                    d2.append(float(response))
                    break
                except ValueError:
                    print("Pleas enter a number!")
        with c.acquisition():
            data = c.get_data(data_points, channels=[0]) / 1000
        x = np.arange(len(data))
        slope, intercept  = scipy.stats.linregress(x, data)[0:2]
        g = slope * x + intercept
        m = np.ones(len(x)) * data.mean()
        plt.plot(x, data, x, m, x, g)
        plt.show()
        print()
        print("d2: {} mm;   dm: {:.5} mm".format(d2[-1], intercept))
        if choice == 1:
            dm.append(intercept)
        if choice == 2:
            dm[-1] = intercept


#np.save(os.path.join("data", "epsilon_dm.npy"), dm)
#np.save(os.path.join("data", "epsilon_d2.npy"), d2)

