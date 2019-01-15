# ------------------------------------------------------------------------------
#  This file (loader.py) is part of neurone_loader                             -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

import os
import pandas as pd
import numpy as np
from . import neurone as nr
from .lazy import Lazy, preloadable
from .mne_export import MneExportable


class BaseContainer(MneExportable):
    @property
    def sampling_rate(self):
        return self._protocol['meta']['sampling_rate'] if hasattr(self, '_protocol') else None

    @property
    def channels(self):
        return self._protocol['channels'] if hasattr(self, '_protocol') else None


@preloadable
class Phase(BaseContainer):
    """
    Properties:
        - data: recorded data with shape (samples, channels) in µV
    """
    def __init__(self, path, phase, protocol=None):
        self.path = path
        self.number = phase['number']
        if protocol is None:
            self._protocol = nr.read_neurone_protocol(self.path)
        else:
            self._protocol = protocol
        self.time_start = phase['time_start']
        self.time_stop = phase['time_stop']

    @Lazy
    def events(self):
        return pd.DataFrame(nr.read_neurone_events(self.path, self.number, self.sampling_rate)['events'])
    
    @property
    def event_codes(self):
        return np.unique(self.events['Code'].values) if 'Code' in self.events else []

    @Lazy
    def data(self):
        return nr.read_neurone_data(self.path, self.number, self._protocol) / 1000  # data is nanovolts

    @Lazy
    def n_samples(self):
        return nr.read_neurone_data_info(self.path, self.number, self._protocol).n_samples

    @Lazy
    def n_channels(self):
        return nr.read_neurone_data_info(self.path, self.number, self._protocol).n_channels

    def clear_data(self):
        del self.data


@preloadable
class Session(BaseContainer):
    def __init__(self, path):
        self.path = path
        self._protocol = nr.read_neurone_protocol(self.path)
        self._get_meta()

    def _get_meta(self):
        self.time_start = self._protocol['meta']['time_start']
        self.time_stop = self._protocol['meta']['time_stop']
        assert len(self._protocol['phases']) > 0, \
            "Session at {} has no phases".format(self.path)
        self.phases = [Phase(self.path, p, self._protocol) for p in self._protocol['phases']]

    @property
    def event_codes(self):
        return np.unique(np.concatenate([phase.event_codes for phase in self.phases]))

    @Lazy
    def data(self):
        phases = sorted(self.phases, key=lambda p: p.number)
        new_array = None
        slices = []
        for p in phases:
            if new_array is None:
                new_array = p.data
                slices.append((0, len(p.data)))
            else:
                old_length = len(new_array)
                shape = list(new_array.shape)
                shape[0] += len(p.data)
                new_array.resize(shape)
                new_array[-len(p.data):] = p.data
                slices.append((old_length, old_length + len(p.data)))
            del p.data

        for index, p in enumerate(phases):
            start, stop = slices[index]
            p.data = new_array[start:stop]

        return new_array

    def clear_data(self):
        for p in self.phases:
            p.clear_data()
        del self.data

    @property
    def events(self):
        phases = sorted(self.phases, key=lambda p: p.number)
        all_events = [phases[0].events]
        current_samples = phases[0].n_samples
        for i in range(1, len(phases)):
            if len(phases[i].events) > 0:
                cur_events = phases[i].events.copy()
                cur_events['StartSampleIndex'] += current_samples
                cur_events['StopSampleIndex'] += current_samples
                cur_time = int(current_samples / self.sampling_rate)
                cur_events['StartTime'] += cur_time
                cur_events['StopTime'] += cur_time
                current_samples += phases[i].n_samples
                all_events.append(cur_events)
        return pd.concat(all_events)
        
    @property
    def n_samples(self):
        return sum([p.n_samples for p in self.phases])

    @property
    def n_channels(self):
        assert len(set([p.n_channels for p in self.phases])) <= 1, \
               "The number of channels shouldn't change between phases"
        return self.phases[0].n_channels if len(self.phases) > 0 else 0


@preloadable
class Recording(BaseContainer):
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
        assert len(session_dirs) > 0, "No sessions found in {}".format(self.path)
        self.sessions = [Session(path) for path in session_dirs]

    @property
    def event_codes(self):
        return np.unique(np.concatenate([session.event_codes for session in self.sessions]))

    @Lazy
    def data(self):
        sessions = sorted(self.sessions, key=lambda x: x.time_start)
        new_array = None
        slices = []
        all_phase_slices = []
        for s in sessions:
            old_length = len(new_array) if new_array is not None else 0
            new_length = old_length + len(s.data)
            del s.data

            phases = sorted(s.phases, key=lambda p: p.number)
            phase_slices = []
            for p in phases:
                if new_array is None:
                    new_array = np.copy(p.data)
                    phase_slices.append((0, len(p.data)))
                else:
                    old_length = len(new_array)
                    shape = list(new_array.shape)
                    shape[0] += len(p.data)
                    new_array.resize(shape)
                    new_array[-len(p.data):] = p.data
                    phase_slices.append((old_length, old_length + len(p.data)))
                del p.data
            all_phase_slices.append(phase_slices)
            slices.append((old_length, new_length))

        for s_index, s in enumerate(sessions):
            for p_index, p in enumerate(s.phases):
                start, stop = all_phase_slices[s_index][p_index]
                p.data = new_array[start:stop]
            start, stop = slices[s_index]
            s.data = new_array[start:stop]

        return new_array

    def clear_data(self):
        for s in self.sessions:
            s.clear_data()
        del self.data

    @property
    def events(self):
        sessions = sorted(self.sessions, key=lambda x: x.time_start)
        assert len(set([s.sampling_rate for s in sessions])) >= 1, \
            'Loading Sessions with different sampling rates is not supported at this time'
        sampling_rate = sessions[0].sampling_rate
        all_events = [sessions[0].events]
        current_samples = sessions[0].n_samples
        for i in range(1, len(sessions)):
            if len(sessions[i].events) > 0:
                cur_events = sessions[i].events.copy()
                cur_events['StartSampleIndex'] += current_samples
                cur_events['StopSampleIndex'] += current_samples
                cur_time = int(current_samples / sampling_rate)
                cur_events['StartTime'] += cur_time
                cur_events['StopTime'] += cur_time
                current_samples += sessions[i].n_samples
                all_events.append(cur_events)
        return pd.concat(all_events)

    @property
    def n_samples(self):
        return sum([s.n_samples for s in self.sessions])

    @property
    def n_channels(self):
        assert len(set([s.n_channels for s in self.sessions])) <= 1, \
               "The number of channels shouldn't change between sessions"
        return self.sessions[0].n_channels if len(self.sessions) > 0 else 0

    @property
    def sampling_rate(self):
        assert len(set([s.sampling_rate for s in self.sessions])) <= 1, \
               "The sampling rate shouldn't change between sessions"
        return self.sessions[0].sampling_rate if len(self.sessions) > 0 else 0

    @property
    def channels(self):
        assert len(set([''.join(s.channels) for s in self.sessions])) <= 1, \
               "Channel names shouldn't change between sessions"
        return self.sessions[0].channels if len(self.sessions) > 0 else 0