# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 11:42:18 2020

@author: pud
"""



#from pt3_read import t3r;
from t3r_read import t3r
from tdms_read import tdms
import pylab as plt
import os;
import tkinter as tk
from tkinter import filedialog
from zoom import zoom_factory;
import numpy as np;
from matplotlib.widgets import Slider,SpanSelector
import IPython

shell = IPython.get_ipython()
shell.enable_matplotlib(gui='qt')


#get the file name
root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename();
filename = os.path.abspath(file_path);
labelz = file_path;

#setup reading of t3r file
ms = 1e-3;
bins = 10 * ms;
zoom_bins = 1 * ms;
file = tdms(filename)

#get the time trace
T,F = file.rebin(bins)

x = T;
y = F/bins;

#create plot
fig = plt.figure(figsize=(24, 6))
ax = fig.add_subplot(221, facecolor='#FFFFCC')

ax.plot(x,y);

ax2 = fig.add_subplot(223, facecolor='#FFFFCC')
line2, = ax2.plot(x,y ,'-');

ax3 = fig.add_subplot(122);
line3, = ax3.loglog(x,y);

#So, 3 subplots made of the same timetrace
#next we select an area to zoom in on and make a FFT of
scale = 1.1 #What does this value do??
f = zoom_factory(ax2,base_scale = scale)  ;

def onselect(xmin, xmax):
    time, trace  = file.TimetraceRange(xmin,xmax,zoom_bins);
    trace = trace/zoom_bins;
    
    thisx = time
    thisy = trace
    line2.set_data(thisx, thisy)
    ax2.set_xlim(thisx[0], thisx[-1])
 
    ax2.set_ylim(thisy.min(), thisy.max())
   
    fig.canvas.draw()

#From here it was in SymphotimeFileReadOneAndPlot that did a weird symmetric FFT
        #Lets try to change this
    
    ffty = np.abs(np.fft.fft(thisy));
   
    freqaxis = np.arange(0,np.shape(ffty)[0],1)/zoom_bins/np.shape(thisy)[0]; #I have to understand this one
    
    line3.set_data(freqaxis, ffty);
    ax3.set_xlim(freqaxis[0]/2,freqaxis[-1]/2)
    ax3.set_ylim(ffty.min(), ffty.max())
    
# t = np.arange(256)
# sp = np.fft.fft(np.sin(t))
# freq = np.fft.fftfreq(t.shape[-1])
# plt.plot(freq, sp.real, freq, sp.imag)   
    


# set useblit True on gtkagg for enhanced performance
span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                    rectprops=dict(alpha=0.5, facecolor='red'))


ax2.set_ylabel('Counts / sec (1/s)');
ax.set_ylabel('Counts / sec (1/s)');
ax.set_xlabel('Time (s)');
ax2.set_xlabel('Time (s)');
ax3.set_xlabel('Frequency (Hz)');
ax3.set_ylabel('Power spectral density (1/Hz)');

plt.show();

