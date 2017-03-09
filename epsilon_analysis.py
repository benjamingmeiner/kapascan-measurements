import os
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

dm = np.load(os.path.join("data", "epsilon_dm.npy"))
d2 = np.load(os.path.join("data", "epsilon_d2.npy"))

# remove duplicate measurements
index_skip = []
for i in range(1, len(dm)):
    if d2[i] == d2[i-1]:
        index_skip.append(i-1)
index_skip += [25, 24]
index = [i for i in range(len(dm)) if i not in index_skip]

dm = dm[index]
d2 = d2[index]

x = d2
y = dm

slope, intercept  = scipy.stats.linregress(x, y)[0:2]

epsilon1 = 1.000576
epsilon2 = epsilon1 / (slope + 1)

print(epsilon2)

xg = np.array([-2, 2])
g = slope * xg + intercept

#plt.figure(figsize=(4,5))
plt.plot(xg, g, x, y, 'xr')
plt.axes().set_aspect(1)
plt.xlim([-0.1, 1.5])
plt.ylim([0.9, 2.1])
plt.grid()
plt.xlabel("$d_m$ [mm]")
plt.ylabel("$d_2$ [mm]")

value_text = ("$s=${:.4}\n".format(slope) +
               "$t=${:.4} mm \n".format(intercept) + 
               "$\\varepsilon_2=\\frac{\\epsilon_1}{s + 1}=$" + "{:.4}".format(epsilon2))

plt.text(0.07, 1.1, value_text, bbox={'facecolor':'white', 'pad':7})


plt.savefig(os.path.join("figures", "epsilon_analysis.png"), dpi=300)


