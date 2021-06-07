





import numpy as np

header_count = 1
header_dtype = np.dtype([
        ('Ident',             'S16'   ),
        ('SoftwareVersion',     'S6'    ),
        ('HardwareVersion',     'S6'    ),
        ('FileTime',          'S18'   ),
        ('CRLF',              'S2'    ),
        ('Comment',           'S256'  ),
        ('NumberOfChannels',   'int32'),
        ('NumberOfCurves',    'int32' ),
        ('BitsPerChannel',     'int32' ),   # bits in each T3 record
        ('RoutingChannels',   'int32' ),
        ('NumberOfBoards',    'int32' ),
        ('ActiveCurve',       'int32' ),
        ('MeasurementMode',   'int32' ),
        ('SubMode',           'int32' ),
        ('RangeNo',           'int32' ),
        ('Offset',            'int32' ),
        ('AcquisitionTime',   'int32' ),   # in ms
        ('StopAt',            'uint32'),
        ('StopOnOvfl',        'int32' ),
        ('Restart',           'int32' ),
        ('DispLinLog',        'int32' ),
        ('DispTimeAxisFrom',  'int32' ),
        ('DispTimeAxisTo',    'int32' ),
        ('DispCountAxisFrom', 'int32' ),
        ('DispCountAxisTo',   'int32' ),])

dispcurve_count = 8
dispcurve_dtype = np.dtype([
        ('DispCurveMapTo', 'int32'),
        ('DispCurveShow',  'int32')])

params_count = 3
params_dtype = np.dtype([
        ('ParamStart', 'f4'),
        ('ParamStep',  'f4'),
        ('ParamEnd',   'f4')])

repeat_count = 1
repeat_dtype = np.dtype([
        ('RepeatMode',      'int32'),
        ('RepeatsPerCurve', 'int32'),
        ('RepeatTime',       'int32'),
        ('RepeatWaitTime',  'int32'),
        ('ScriptName',      'S20'  )])

hardware_count = 1
hardware_dtype =  np.dtype([
        ('BoardSerial',     'int32'),
        ('CFDZeroCross',   'int32'),
        ('CFDDiscriminatorMin',   'int32'),
        ('SYNCLevel',       'int32'),
        ('CurveOffset',       'int32'),
        ('Resolution',      'f4')])

ttmode_count = 1
ttmode_dtype = np.dtype([
        ('TTTRGlobclock',      'int32' ),
        ('ExtDevices',      'int32' ),
        ('Reserved1',       'int32' ),
        ('Reserved2',       'int32' ),
        ('Reserved3',       'int32' ),
        ('Reserved4',       'int32' ),
        ('Reserved5',       'int32' ),
        ('SyncRate',        'int32' ),
        ('AverageCFDRate',        'int32' ),
        ('StopAfter',       'int32' ),
        ('StopReason',      'int32' ),
        ('nRecords',        'int32' ),
        ('ImgHdrSize',      'int32')])

t3r_dtype = np.dtype([('timetag','uint16'), ('datflag','uint16')])
#================================================================
class t3r:
    def __init__(self,filename,photon_bit = 15, overfl_bit = 12):
        with open(filename,'rb') as f:
            self.header     =   np.fromfile(f, dtype = header_dtype,    count = header_count)
            self.dispcurve  =   np.fromfile(f, dtype = dispcurve_dtype, count = dispcurve_count)
            self.params     =   np.fromfile(f, dtype = params_dtype,    count = params_count)
            self.repeat     =   np.fromfile(f, dtype = repeat_dtype,    count = repeat_count)
            self.hardware   =   np.fromfile(f, dtype = hardware_dtype,  count = hardware_count)
            self.ttmode     =   np.fromfile(f, dtype = ttmode_dtype,    count = ttmode_count)
            self.ImgHdr     =   np.fromfile(f, dtype='int32',           count = self.ttmode['ImgHdrSize'][0])
            self.t3records  =   np.fromfile(f, dtype = t3r_dtype)

            self.T_unit = self.ttmode['TTTRGlobclock']*1e-9
            self.t_unit = self.hardware['Resolution']
            
            self.photon_flag = np.right_shift(np.bitwise_and(self.t3records['datflag'], 2**(photon_bit -1)), photon_bit-1)
            self.overfl_flag = np.right_shift(np.bitwise_and(self.t3records['datflag'], 2**(overfl_bit -1)), overfl_bit-1)

            self.T = self.t3records['timetag'].astype(np.int64) + np.cumsum((1-self.photon_flag)*self.overfl_flag, dtype=np.int64)*(2**16) #dtype=np.int64 was added to this line by Xuxing
            self.T = self.T[self.photon_flag==1]
            
            self.t = np.bitwise_and(self.t3records['datflag'], 2**overfl_bit-1).astype(np.int32)
            self.t = self.header['NumberOfChannels']-self.t[self.photon_flag==1]
            

    def Time(self):
        return self.T, self.T_unit
    
    def time(self):
        return self.t, self.t_unit

    def Timetrace(self, binstime):
        T = self.T * self.T_unit
        x = np.arange(0,np.max(T),binstime)
        y,x = np.histogram(T,x)
        return x[1:], y
    
    def TimetraceRange(self, t_start,t_end, binstime):
        T = self.T * self.T_unit;
        T=T[(T>=t_start)&(T<=t_end)]
        x = np.arange(np.min(T),np.max(T),binstime)
        y,x = np.histogram(T,x)
        return x[1:], y
    
    def LifetimeFlt(self,binstime,tmin,tmax,tNmin,tNmax):
        T = self.T[np.logical_and(self.t*self.t_unit>=tmin, self.t*self.t_unit<=tmax)]*self.T_unit
        TN = self.T[np.logical_and(self.t*self.t_unit>=tNmin, self.t*self.t_unit<=tNmax)]*self.T_unit
        x = np.arange(0,np.max(T),binstime)
        y,x = np.histogram(T,x)
        yN,x = np.histogram(TN,x)
        return x[1:], y, y/yN*np.mean(yN)
    
    def Timeweights(self, binstime,t0):
        T = self.T * self.T_unit
        x = np.arange(0,np.max(T),binstime)
        y,x = np.histogram(T,x,weights = self.t*self.t_unit-t0)
        return x[1:], y

    def Decay(self):
        x,y = np.unique(self.t, return_counts=True)
        return self.t_unit*x, y
    
    def fastFCS(self,minT,maxT,NT):
        tau = np.logspace(np.log10(minT),np.log10(maxT),NT)/self.T_unit
        G = np.zeros(len(tau))
        Tmax = max(self.T)
        for i in np.arange(len(tau)):
            T0 = self.T[self.T<=Tmax-tau[i]]
            Tt = self.T[self.T>tau[i]] - tau[i]
            bins = np.arange(min(T0),max(T0),0.9*tau[i])
            I0,t0 = np.histogram(T0,bins)
            It,tt = np.histogram(Tt,bins)
            G[i] = np.mean((I0-np.mean(I0))*(It-np.mean(It)))/(np.mean(I0)*np.mean(It))
        return tau*self.T_unit,G

