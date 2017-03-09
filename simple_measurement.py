import sys, os
sys.path.append(os.path.join(os.path.abspath(''), os.path.pardir, 'kapascan')
import controller
import matplotlib.pyplot as plt

host = '192.168.254.173'
data_points = 2000
sampling_time = 1  # ms
c = controller.Controller(2000, host)
data = c.acquire(data_points, sampling_time, channels=[0]) / 1000

plt.plot(data)
print(data.mean())

