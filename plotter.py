import numpy as np;
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import mplcursors
import csv
import copy
import dateutil.parser as dateparser
import datetime

from tdms_read import tdms
from log_entry import LogEntry
from utils import read_interval_from_multiple_files, AbstractCountsFile, COUNTS, INPUT_EXT


class Plotter:
    
    xmin = 0
    xmax = 1 
    

    def __init__(self, abstractfile, seconds_in_file=None, file_interval=(0,1), bin=10e-3):
        self.abstractfile = abstractfile
        
        self.logfile = self.abstractfile.dir + self.abstractfile.basename + '_logfile.csv'
        self.log_loaded = self.load_log()
              
        if not seconds_in_file:
            self.seconds_in_file = self.calc_seconds_in_file()
        else:
            self.seconds_in_file = seconds_in_file
           
        self.file_interval = np.arange(file_interval[0], file_interval[1])
     
        self.binsize = bin
        self.translate_x = self.file_interval[0] * self.seconds_in_file
       
           
    def init_figure(self):
        self.fig, axes = plt.subplots(2, figsize=(10,10))
        self.input_ax = axes[0]
        self.log_ax = self.input_ax.twinx()
        self.main_ax = self.input_ax.twinx()
        self.log_ax.get_shared_y_axes().join(self.log_ax, self.input_ax)
        self.fft_ax = axes[1]
        
        self.main_ax.yaxis.set_label_position('left')
        self.main_ax.yaxis.set_ticks_position('left')
        
        self.input_ax.yaxis.set_label_position('right')
        self.input_ax.yaxis.set_ticks_position('right')
                
        self.log_ax.set_zorder(3)
        self.input_ax.set_zorder(1)
        self.main_ax.set_zorder(2)
         
        # log_ax has to be used because events are registered on axis added last
        self.span = SpanSelector(self.log_ax, self.onselect, 'horizontal', useblit=True,
                                rectprops=dict(alpha=0.5, facecolor='red'))
	
    
    def plot_counts(self):
        counts_t = np.array([0])
        counts = np.array([])
        
        for f in self.file_interval:
            fn = self.abstractfile.filename(COUNTS, f)
            file = tdms(fn)
            
            cx, cy = file.rebin(self.binsize)
            cx = cx + counts_t[-1]
            cy = cy / self.binsize
            
            range = min(len(cx), len(cy))
            
            counts_t = np.append(counts_t, cx[:range])
            counts = np.append(counts, cy[:range])
            
            if len(cx) != len(cy):
                print('unequal: ', fn)
    
        counts_t = np.delete(counts_t, 0)
        self.main_ax.plot(counts_t + self.translate_x, counts, color='r')
        self.main_ax.set_xlim(self.file_interval[0]*self.seconds_in_file,
                              (self.file_interval[-1]+1)*self.seconds_in_file)
        
    
    def plot_input(self, input_binsize, yscale, yoffset=0, plot_log=True, log_offset=0):
        time = np.array([0])
        volt = np.array([])
        
        shift = None
    
        for f in self.file_interval:
            fn = self.abstractfile.filename(INPUT_EXT, f)
            file = tdms(fn, INPUT_EXT)
            
            vx, vy = file.rebin(self.binsize)
            vx = vx + time[-1]
            
            range = min(len(vx), len(vy))
            
            time = np.append(time, vx[:range])
            volt = np.append(volt, vy[:range])
            
            if not shift:
                shift = vx[-1] - vx[0]
            
        time = np.delete(time, 0)
  
        self.input_ax.plot(time + self.translate_x, -volt*yscale + yoffset, color='b')
        
        if plot_log and self.log_loaded:
            offset = self.file_interval[0] * shift - log_offset
            self.log_ax.scatter(self.log_x - offset+ self.translate_x, self.log_y, color='g')
            self.log_ax.plot(self.log_x - offset + self.translate_x, self.log_y, color='g', drawstyle='steps-post')
            
            cursor = mplcursors.cursor(self.log_ax,hover=mplcursors.HoverMode.Transient)
            @cursor.connect("add")
            def on_add(sel):
                if self.log_ax.get_visible():
                    sel.annotation.set(text=self.log_annotations[int(sel.target.index.int)], zorder=100)
                    print(type(sel))
            
            self.log_ax.set_xlim(0, time[-1])
        
        self.main_ax.set_xlim(self.file_interval[0]*self.seconds_in_file,
                              (self.file_interval[-1]+1)*self.seconds_in_file)
    
    def fft(self, fft_bin):
        time, trace  = read_interval_from_multiple_files(AbstractCountsFile(self.abstractfile),
                                                        self.seconds_in_file, self.xmin,self.xmax, 
                                                        fft_bin);
        trace = trace/fft_bin

        fft_y = np.abs(np.fft.fft(trace))
        fft_x = np.arange(0, np.shape(fft_y)[0], 1) / fft_bin / np.shape(trace)[0];
           
        self.fft_ax.clear();
        self.fft_ax.loglog(fft_x, fft_y)
        
	
    def calc_seconds_in_file(self):
        fn = self.abstractfile.filename(COUNTS, 0)
        file = tdms(fn)
            
        cx, cy = file.rebin(0.1)
        seconds = round(cx[-1], 1)
        return seconds
    
    
    def set_file_interval(self, _min, _max):
        self.file_interval = np.arange(_min, _max)
        self.translate_x = self.file_interval[0] * self.seconds_in_file
    
    def re_draw(self):
        pass


    def load_log(self):
        self.log_x = []
        self.log_y = []
        self.log_annotations = []

        with open(self.logfile) as file:
            log = csv.DictReader(file)
            
            raw_entries = []
            for entry in log:
                raw_entries.append(entry)
            virtual_entry = copy.copy(raw_entries[-1])
            virtual_datetime = dateparser.parse(virtual_entry['timestamp'])+datetime.timedelta(seconds=100)
            virtual_entry['timestamp'] = virtual_datetime.isoformat()
            raw_entries.append(virtual_entry)

            self.log_entries = []
            datetime_0 = dateparser.parse(raw_entries[0]['timestamp'])
            for i in range(len(raw_entries)-1):
                prev = self.log_entries[i-1] if i > 0 else None;
                entry = LogEntry(raw_entries[i], raw_entries[i+1], prev, datetime_0);
                self.log_entries.append(entry);
                self.log_annotations.append(entry.annotation_builder())
                self.log_x.append(entry.t_start)
                self.log_y.append(entry.voltage if entry.channel else 0)
        
        self.log_x = np.array(self.log_x)
        self.log_y = np.array(self.log_y)
        
        return True


    def set_display_input(self, disp):
        self.input_ax.set_visible(disp)
        self.log_ax.set_visible(disp)
    
        self.set_spanselect_axis(disp)
        
                                
    def set_display_log(self, disp):
        self.log_ax.set_visible(disp)
        self.set_spanselect_axis(disp)

    def set_spanselect_axis(self, disp_log):
        span_ax = self.log_ax if disp_log else self.main_ax
    
        self.span = SpanSelector(span_ax, self.onselect, 'horizontal', useblit=True,
                                rectprops=dict(alpha=0.5, facecolor='red'))

    def onselect(self, _xmin, _xmax):
        self.xmin = _xmin
        self.xmax = _xmax
        print('Selected interval: [%3.3f, %3.3f], length: %3.3f seconds' % (self.xmin, self.xmax, self.xmax-self.xmin))

    
    # this currently doesn't do anything
    # def on_graph_values(self, event):
    #     if self.xmin is None or self.xmax is None:
    #         print("Interval not yet selected")
    #         return
                

    #     input_sgn_bin = 1e-6 * 2000

    #     time, counts  = file.TimetraceRange(self.xmin, self.xmax, bins);
    #     time2, volttrace = file2.TimetraceRange(self.xmin, self.xmax, input_sgn_bin)
    #     counts = counts/bins;
    #     volttrace = volttrace/input_sgn_bin;

    #     # fig, (ax1, ax2) = plt.subplots(1, 2)
    #     fig = plt.figure(figsize=(24, 8))

    #     axis1 = fig.add_subplot(111)
    #     axis2 = axis1.twinx()
    #     #         axis2 = fig.add_subplot(110)

    #     # fft_line = axis2.plot()

    #     #for axis in 'left', 'bottom':
    #     # timetrace_line.set_linewidth(2)
    #     axis1.tick_params(axis='both', which='both', labelsize=26)
    #     axis2.tick_params(axis='y', which='both', labelsize=26)
    #     axis1.set_xlabel('Time (s)',  fontsize = 32)
    #     axis1.set_ylabel('Counts per second',  fontsize = 32)
    #     axis2.set_ylabel('AC voltage (V)', fontsize= 32)
    #     axis2.set_ylim(0,6)
    #     voltage_line, = axis2.plot(time2, -(volttrace)/4800-1.5,'-', color='orange');
    #     timetrace_line, = axis1.plot(time, counts ,'-');
    #     timetrace_line.tick_params(axis='both', which='major', labelsize=20, width=2.5, length=10)
    #     plt.show()


    #     figure = plt.figure()
    #     plt.scatter(amplitudes, averages)
    #     plt.show()