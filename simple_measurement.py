from kapascan.controller import Controller
import matplotlib.pyplot as plt

sensor = '2011'
host = '192.168.254.173'

data_points = 2000
sampling_time = 0.256  # ms
c = Controller(sensor, host)

with c:
    with c.acquisition('continuous', sampling_time):
        data = c.get_data(data_points, channels=[0]) / 1000

plt.plot(data)
