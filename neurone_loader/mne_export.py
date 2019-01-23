# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (mne_export.py) is part of neurone_loader                         -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------
"""
Provides the metaclass `MneExportable` that allows subclasses implementing all the metaclass's properties
to be converted to a `mne.io.RawArray`.
"""

import logging
import numpy as np
import abc
from copy import deepcopy

logger = logging.getLogger(__name__)

# compatible with Python 2 *and* 3:
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})


class MneExportable(ABC):
    """

    A metaclass that provides a function allowing objects that expose data, events, channels and sampling_rate
    properties to be converted to an mne.io.RawArray.

    """

    def _import_mne(self):
        try:
            # noinspection PyPackageRequirements
            import mne
            self._mne = mne
            return True
        except ImportError:
            logger.error("To convert data to an MNE object you must install MNE "
                         "and all its dependencies.")
            return False

    def to_mne(self, substitute_zero_events_with=None, copy=False):
        """
        Convert loaded data to a mne.io.RawArray

        :param substitute_zero_events_with: None. events with code = 0 are not supported by MNE, if this parameter is
                                            set, the event code 0 will be substituted with this parameter
        :param copy: False. If False, the original data will be removed from memory to save space while creating the
                     mne.io.RawArray. If the data is needed again it must be reloaded from disk
        :type substitute_zero_events_with: None or int
        :type copy: bool
        :return: the converted data
        :rtype: mne.io.RawArray
        :raises ImportError: if the mne package is not installed
        """

        if not hasattr(self, '_mne'):
            if not self._import_mne():
                raise ImportError
        mne = self._mne

        events = self.events

        def _channel_type(name):
            mappings = [
                (['emg'], 'emg'),
                (['eog'], 'eog'),
                (['ecg'], 'ecg'),
                (['Microphone'], 'bio'),
                (_default_eeg_channel_names, 'eeg')
            ]
            for starts, ch_type in mappings:
                for start in starts:
                    if name.lower().startswith(start.lower()):
                        return ch_type
            logger.warning('Channel {channel} will be classified as EEG channel '
                           'but is not in the list of common EEG channel names'
                           .format(channel=name))
            return 'eeg'

        channel_types = list(map(_channel_type, self.channels))
        assert len(channel_types) == len(self.channels)

        data_length = self.data.T.shape[1]
        data_dtype = self.data.dtype

        ssc = [(start, stop, code) for (start, stop, code)
               in events[['StartSampleIndex', 'StopSampleIndex', 'Code']].values]

        if substitute_zero_events_with is not None:
            event_codes = np.unique(events['Code'].values)
            assert type(substitute_zero_events_with) is int, 'substitute_zero_events_with must be int or None'
            assert substitute_zero_events_with not in event_codes, \
                """the original data can't contain event with code
                substitute_zero_events_with ({})""".format(substitute_zero_events_with)

        stim_channel_names = ['STI 014']
        stim_channels = [np.zeros(data_length, dtype=data_dtype)]

        def _add_stim_channel():
            index = len(stim_channel_names)
            stim_channel_names.append('STI {:03g}'.format(index + 14))
            stim_channels.append(np.zeros(data_length, dtype=data_dtype))

        for start, stop, code in ssc:
            channel_index = 0
            if substitute_zero_events_with is not None:
                if code == 0:
                    code = substitute_zero_events_with
            else:
                assert code != 0, "events with event code 0 are not supported by MNE, use the " \
                                  "substitute_zero_events_with parameter of this method to substitute with an " \
                                  "alternative code"

            corrected_start = start - 1 if start != 0 else 0  # sample before event start needs to be 0
            while not (stim_channels[channel_index][corrected_start:stop + 1] == 0).all():
                channel_index += 1
                if channel_index >= len(stim_channels):
                    _add_stim_channel()

            if channel_index != 0:
                logger.warning('Event (code {current_code}) has a concurrent event between samples ({start}) and '
                               '({stop}). An additional stim channel will be used/created: ({channel}).'
                               .format(current_code=code, start=start, stop=stop,
                                       channel=stim_channel_names[channel_index]))

            stim_channels[channel_index][start:stop + 1] += code  # event must be at least one sample long

        stim_info = mne.create_info(ch_names=stim_channel_names,
                                    sfreq=self.sampling_rate,
                                    ch_types='stim')

        stim_cnt = mne.io.RawArray(stim_channels, stim_info, verbose='WARNING')

        channel_names = deepcopy(self.channels)
        channel_names.extend(stim_channel_names)
        all_channel_types = deepcopy(channel_types)
        all_channel_types.extend(['stim' for _ in stim_channel_names])

        info = mne.create_info(ch_names=self.channels,
                               sfreq=self.sampling_rate,
                               ch_types=channel_types)

        # data is µV samples x channels, mne needs V channels x samples
        data = self.data.T / (1000 * 1000)
        cnt = mne.io.RawArray(data, info)
        if not copy:
            self.clear_data()

        cnt = cnt.add_channels([stim_cnt])

        return cnt

    @property
    @abc.abstractmethod
    def data(self):
        """
        Abstract Property

        :return: should contain data in (n_samples, n_channels) shape
        :rtype: numpy.ndarray
        """

    @abc.abstractmethod
    def clear_data(self):
        """
        Abstract Method

        Should delete loaded data from memory
        """

    @property
    @abc.abstractmethod
    def events(self):
        """
        Abstract Property

        :return: should contain the events as a DataFrame, required fields are `StartSampleIndex`, `StopSampleIndex`
                 and `Code`. Additional fields are ignored.
        :rtype: pandas.DataFrame
        """

    @property
    @abc.abstractmethod
    def channels(self):
        """
        Abstract Property

        :return: should contain the names of channels, matching the sequence used in the data property
        :rtype: list[str]
        """

    @property
    @abc.abstractmethod
    def sampling_rate(self):
        """
        Abstract Property

        :return: should contain the used sampling rate
        :rtype: int
        """


_default_eeg_channel_names = ['Fp1', 'Fpz', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'FC5', 'FC1', 'FC2', 'FC6', 'M1', 'T7',
                              'C3', 'Cz', 'C4', 'T8', 'M2', 'CP5', 'CP1', 'CP2', 'CP6', 'P7', 'P3', 'Pz', 'P4', 'P8',
                              'POz', 'O1', 'Oz', 'O2', 'AF7', 'AF3', 'AF4', 'AF8', 'F5', 'F1', 'F2', 'F6', 'FC3', 'FCz',
                              'FC4', 'C5', 'C1', 'C2', 'C6', 'CP3', 'CPz', 'CP4', 'P5', 'P1', 'P2', 'P6', 'PO5', 'PO3',
                              'PO4', 'PO6', 'FT7', 'FT8', 'TP7', 'TP8', 'PO7', 'PO8', 'FT9', 'FT10', 'TPP9h', 'TPP10h',
                              'PO9', 'PO10', 'P9', 'P10', 'AFF1', 'AFz', 'AFF2', 'FFC5h', 'FFC3h', 'FFC4h', 'FFC6h',
                              'FCC5h', 'FCC3h', 'FCC4h', 'FCC6h', 'CCP5h', 'CCP3h', 'CCP4h', 'CCP6h', 'CPP5h', 'CPP3h',
                              'CPP4h', 'CPP6h', 'PPO1', 'PPO2', 'I1', 'Iz', 'I2', 'AFp3h', 'AFp4h', 'AFF5h', 'AFF6h',
                              'FFT7h', 'FFC1h', 'FFC2h', 'FFT8h', 'FTT9h', 'FTT7h', 'FCC1h', 'FCC2h', 'FTT8h', 'FTT10h',
                              'TTP7h', 'CCP1h', 'CCP2h', 'TTP8h', 'TPP7h', 'CPP1h', 'CPP2h', 'TPP8h', 'PPO9h', 'PPO5h',
                              'PPO6h', 'PPO10h', 'POO9h', 'POO3h', 'POO4h', 'POO10h', 'OI1h', 'OI2h']
