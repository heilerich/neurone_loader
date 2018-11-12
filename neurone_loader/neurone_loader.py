# This file is part of neurone_loader
# (https://www.github.com/heilerich/neurone_loader)
# Copyright © 2018 Felix Heilmeyer.
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
# Please see the file LICENSE for details.

import os
import pandas as pd
import numpy as np
import utilities_neurone as nr
from lazy import lazy, preloadable

@preloadable
class Phase:
    def __init__(self, path, number, protocol=None):
        self.path = path
        self.number = number
        self._protocol = protocol
    
    @lazy
    def events(self):
        return pd.DataFrame(nr.read_neurone_events(self.path, self.number, self._protocol['meta']['sampling_rate'])['events'])
    
    @lazy
    def event_codes(self):
        return np.unique(self.events['Code'].values) if 'Code' in self.events else []
    
    @lazy
    def data(self):
        return nr.read_neurone_data(self.path, self.number, self._protocol)
        
@preloadable
class Session:
    def __init__(self, path):
        self.path = path
        self._get_meta()
        
    def _get_meta(self):
        self._protocol = nr.read_neurone_protocol(self.path)
        self.channels = self._protocol['channels']
        self.sampling_rate = self._protocol['meta']['sampling_rate']
        self.time_start = self._protocol['meta']['time_start']
        self.time_stop = self._protocol['meta']['time_stop']
        self.phases = [Phase(self.path, n, self._protocol) for n in self._protocol['phases']]
    
    @lazy
    def event_codes(self):
        return np.unique(np.concatenate([phase.event_codes for phase in self.phases]))

@preloadable
class Recording:
    """
    A recording
    """
    def __init__(self, path):
        self.path = path
        self._find_sessions()
        
    def _find_sessions(self):
        session_dirs = [os.path.join(self.path, dirname)
                        for dirname in os.listdir(self.path) 
                        if os.path.isdir(os.path.join(self.path, dirname)) 
                            and 'Protocol.xml' in os.listdir(os.path.join(self.path, dirname))]
        self.sessions = [Session(path) for path in session_dirs]
    
    @lazy
    def event_codes(self):
        return np.unique(np.concatenate([session.event_codes for session in self.sessions]))