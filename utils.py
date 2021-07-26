import numpy as np
from tdms_read import tdms


INPUT_EXT = '_output_monitoring_analog_input'
TDMS = '.tdms'
COUNTS = '_counts'


def make_extension(index, n_prefix):
    if index == 0:
        extension = ''
    else:
        n = str(index)
        n = '0' + n if len(n) == 1 else n
        extension = n_prefix + n 
    return extension
    

from dataclasses import dataclass

@dataclass
class DIO_event:
    file_index: int
    seconds_in_file: int
    total_seconds: int


class AbstractFile:
    def __init__(self, path, ext_func, n_prefix, extension=TDMS):
        self.base_path = path
        filename_comps = path.split('.')[0].split('\\')
        self.dir = '\\'.join(filename_comps[:-1]) + '\\'
        self.basename = filename_comps[-1][:-len(COUNTS)] # if python 3.9, change to str.removesuffix()
        self.ext_func = ext_func
        self.extension = extension
        self.n_prefix = n_prefix
       
    def filename(self, suffix, index=0):
        return self.dir + self.basename + suffix + self.ext_func(index, self.n_prefix) + self.extension

class AbstractCountsFile(AbstractFile):
    def __init__(self, abstractfile):
        super().__init__(abstractfile.base_path, abstractfile.ext_func, abstractfile.n_prefix, abstractfile.extension)

    def filename(self, index=0):
        return super().filename(COUNTS, index)
        
class AbstractInputFile(AbstractFile):
    def __init__(self, abstractfile):
        super().__init__(abstractfile.base_path, abstractfile.ext_func, abstractfile.n_prefix, abstractfile.extension)

    def filename(self, index=0):
        return super().filename(INPUT_EXT, index)
        
      
def read_interval_from_multiple_files(abstract_file, file_length, _min, _max, bin, channel_name='_counts'):
    n_min = max(int(_min // file_length), 0) 
    n_max = int(_max // file_length) + 1
    left_underflow = (_min % file_length) 
    right_overflow = -(_max % file_length) + file_length
    
    filenames = [abstract_file.filename(i) for i in np.arange(n_min, n_max)]
    
    datax = np.array([0])
    datay = np.array([])
    
    for fn in filenames:
        f = tdms(fn, channel_name)
        fx, fy = f.rebin(bin)
        
        if fx[-1] < file_length *.98:
            right_overflow = bin
        
        fx = fx + datax[-1]
        datax = np.append(datax, fx)
        datay = np.append(datay, fy)
                
    
    datax = np.delete(datax, 0)
    
    left_bound = int(left_underflow/bin)
    right_bound = int(right_overflow/bin)
    
    return datax[left_bound:-right_bound], datay[left_bound:-right_bound]
    
    