import dateutil.parser as dateparser


WAVEFORMS = {
    '0': 'Sine',
    '1': 'Block',
    '2': 'Sawtooth'
}

ANNOTATIONS = {
    'frequency':{'suffix': 'Hz', 'display': True, 'line': 0},
    'mod_depth': {'suffix': '%', 'display': True, 'line': 1},
    'mod_type': {'suffix': '', 'display': True, 'line': 1},
    'mod_freq': {'suffix': 'Hz', 'display': True, 'line': 1},
    'modulation': {'suffix': '', 'display': True, 'line': 1}
}

class LogEntry:
               
    DIO = 'dio0'
    
    def __init__(self, row, next_row, prev_event, datetime_0):
        self.voltage = float(row['ac_volt'])
        self.frequency = float(row['ac_freq'])
        self.modulation = True if row['modulation_enabled'] in ['True', 'true'] else False
        
        self._channel = True if row['channel_enabled'] in ['True', 'true'] else False
        self._dio = True if row[self.DIO] in ['True', 'true'] else False
        self.channel =  self._channel and self._dio
        
        self.mod_depth = float(row['mod_depth'])
        self.mod_type = 'AM' if int(row['mod_type']) == 0 else 'FM'
        self.mod_waveform = WAVEFORMS[row['mod_waveform']]
        self.mod_freq = float(row['mod_freq'])        
        
        self.timestamp_start = row['timestamp']
        self.timestamp_end = next_row['timestamp']
        
        self.datetime_0 = datetime_0
        self.datetime_start = dateparser.parse(self.timestamp_start)
        self.datetime_end = dateparser.parse(self.timestamp_end)
        
        self.t_start = (self.datetime_start - self.datetime_0).total_seconds()
        self.t_end = (self.datetime_end - self.datetime_0).total_seconds()
        
        self.previous_event = prev_event
        
        
    def changes_from_previous(self):
        if self.previous_event is None:
            return []
        tracked_headers = ANNOTATIONS.keys()
        changed_headers = []
        lines = ['', '']
        for header in tracked_headers:
            if getattr(self, header) != getattr(self.previous_event, header):
                changed_headers.append(header)
                if ANNOTATIONS[header]['display']:
                    lines[ANNOTATIONS[header]['line']] += (' %s%s' % (getattr(self, header), ANNOTATIONS[header]['suffix']))

        return lines
        
    
    def annotation_builder(self):
        return '%7iHz %s, %s \n %7iHz, %3.2f%% %s' % (self.frequency, self.mod_type, self.mod_waveform, 
                                                         self.mod_freq, self.mod_depth, self.modulation)
    
        
    def plot(self, axis, offset=0):
        x_start = self.t_start - offset
        x_end = self.t_end - offset
        y = self.voltage if self.channel else 0
        line_style = ':' if self.modulation else '-'
        color = 'b'
        axis.plot([x_start, x_end], [y, y], "-o",linestyle=line_style, color=color,linewidth=3,drawstyle="steps-pre")

            
#    def contained(self, t): # returns: 0 if in range, 1 if larger than range, -1 if smaller than range
#        if t < self.t_start:
#            return -1
#        elif t > self.t_end:
#            return 1
#        else:
#            return 0
            
    
#def find_event_at_time(event_list, t):
#    if len(event_list) == 0:
#        return None;
#    if event_list[0].contained(t) == -1 or event_list[-1].contained(t) == 1:
#        return None;
#    else:
#        middle = int(len(event_list) / 2)
#        result = event_list[middle].contained(t)
#        if result == 0:
#            return event_list[middle]
#        elif result == 1:
#            return find_event_at_time(event_list[middle+1:-1], t)
#        else:
#            return find_event_at_time(event_list[0:middle], t)
        
# def annotate(event_list, t):
#     event = find_event_at_time(event_list, t)
#     if event:
#         return '\n'.join(event.annotation_builder())
        