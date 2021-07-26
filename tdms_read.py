# -*- coding: utf-8 -*-
"""
Created on Mon May 24 15:39:57 2021

@author: PudS

opens files with 
"""

import numpy as np;
from nptdms import TdmsFile;

class tdms :
    
    
    def __init__(self,filename, group_name='_counts'):
        #this opens the file but does not read it to not pollute memory
        self.tdmsfile = TdmsFile.open(filename);
        
        #fetch the channel for counts
        self.group =  self.tdmsfile[group_name]
        self.channel = self.group['Channel 0'];
        self.dt = self.channel.properties['wf_increment'];
        self.channel_NPoints = self.channel._length;
        
        
    def rebin (self, bintime):
        if(bintime<self.dt):    raise Exception('Selected bin time smaller than the sampling time of tdms file');
        points_in_bin = round(bintime/self.dt,3);
        if(points_in_bin %1 != 0):
            raise Exception('Selected bin time should be multiple of sampling time: '+ str(self.dt)+' binning time: '+ str(bintime)+' and points_in_bin='+str(points_in_bin));
        points_in_bin = int(points_in_bin);
        bins_in_trace = np.floor_divide(self.channel_NPoints,points_in_bin).astype(np.int);  
        if(bins_in_trace==0): raise Exception('Timetrace too short for selected bin time');
        self.T = np.arange(0,bins_in_trace*bintime,bintime);
        self.trace = np.zeros(bins_in_trace);
        bin_number = 0;
        while(bin_number<bins_in_trace):
            self.trace[bin_number]=np.sum(self.channel[bin_number*points_in_bin:(bin_number+1)*points_in_bin]);
            bin_number=bin_number+1;
        return self.T,self.trace;
    
    
    def TimetraceRange(self, t_start,t_end, bintime):
         #select time region
        T = np.arange(0,self.channel_NPoints*self.dt,self.dt);
             
        t_start = max(t_start, T[0])
        t_end = min(t_end, T[-1])
        
        T=T[(T>=t_start)&(T<=t_end)];
        if(bintime<self.dt):    raise Exception('Selected bin time smaller than the sampling time of tdms file');
        points_in_bin = round(bintime/self.dt,3);
        if(points_in_bin %1 != 0): raise Exception('Selected bin time should be multiple of sampling time: '+ str(self.dt)+' binning time: '+ str(bintime)+' and points_in_bin='+str(points_in_bin));
        points_in_bin = int(points_in_bin);
        bins_in_trace = np.floor_divide(np.shape(T)[0],points_in_bin).astype(np.int);  
        
        if(bins_in_trace==0): raise Exception('Timetrace too short for selected bin time');
        
        Time = np.arange(0,bins_in_trace*bintime,bintime);
        Trace = np.zeros(bins_in_trace);
        bin_number = 0
        offset = int(np.floor(t_start/self.dt/points_in_bin));
        while(bin_number<bins_in_trace):
            Trace[bin_number]=np.sum(self.channel[(bin_number+offset)*points_in_bin:(bin_number+offset+1)*points_in_bin]);
            bin_number=bin_number+1;
        return Time[:len(Trace)],Trace;
            
        
        