# ------------------------------------------------------------------------------
#  This file (mne_export.py) is part of neurone_loader                         -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2018 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------
"""
This module provides the metaclass `MneExportable` that allows subclasses implementing all the metaclass's properties
to be converted to a mne.io.RawArray.
"""

import logging
import numpy as np
import abc

logger = logging.getLogger(__name__)


class MneExportable(abc.ABC):
    """

    A metaclass that provides a function allowing objects that expose data, events, channels and sampling_rate
    properties to be converted to an mne.io.RawArray.

    """

    @property
    @abc.abstractmethod
    def data(self):
        """
        :return: should contain data in (n_samples, n_channels) shape
        :rtype: numpy.ndarray
        """

    @property
    @abc.abstractmethod
    def events(self):
        """
        :return: should contain the events as a DataFrame, required fields are `StartSampleIndex`, `StopSampleIndex`
        and `Code`. Additional fields are ignored.
        :rtype: pandas.DataFrame
        """

    @property
    @abc.abstractmethod
    def channels(self):
        """
        :return: should contain the names of channels, matching the sequence used in the data property
        :rtype: list[str]
        """

    @property
    @abc.abstractmethod
    def sampling_rate(self):
        """
        :return: should contain the used sampling rate
        :rtype: int
        """

    def _import_mne(self):
        try:
            # noinspection PyPackageRequirements
            import mne
            self._mne = mne
            return True
        except ImportError:
            logger.error("To convert data to an MNE object you must install MNE"
                         "and all its dependencies.")
            return False

    def to_mne(self, substitute_zero_events_with=None):
        """
        Convert loaded data to a mne.io.RawArray
        :param substitute_zero_events_with: events with code = 0 are not supported by MNE, if this parameter is set, the
        event code 0 will be substituted with this parameter
        :type substitute_zero_events_with: None (default) or int
        :return: the converted data
        :rtype: mne.io.RawArray
        :raises ImportError: if the mne package is not installed
        """

        if not hasattr(self, '_mne'):
            if not self._import_mne():
                return
        mne = self._mne

        # data is µV samples x channels, mne needs V channels x samples
        data = (self.data / (1000 * 1000)).T
        events = self.events

        info = mne.create_info(ch_names=self.channels,
                               sfreq=self.sampling_rate,
                               ch_types='eeg')

        cnt = mne.io.RawArray(data, info)

        ssc = [(start, stop, code) for (start, stop, code)
               in events[['StartSampleIndex', 'StopSampleIndex', 'Code']].values]

        if substitute_zero_events_with is not None:
            event_codes = np.unique(events['Code'].values)
            assert type(substitute_zero_events_with) is int, 'substitute_zero_events_with must be int or None'
            assert substitute_zero_events_with not in event_codes, \
                "the original data can't contain event with code substitute_zero_events_with ({})" \
                    .format(substitute_zero_events_with)

        stim_channel_names = ['STI 014']
        stim_channels = [np.zeros_like(cnt.get_data()[0])]

        def _add_stim_channel():
            index = len(stim_channel_names)
            stim_channel_names.append('STI {:03g}'.format(index + 14))
            stim_channels.append(np.zeros_like(cnt.get_data()[0]))

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
            while not (stim_channels[channel_index][corrected_start - 1:stop + 1] == 0).all():
                channel_index += 1
                if channel_index >= len(stim_channels):
                    _add_stim_channel()

            if channel_index != 0:
                logger.warning('Event (code {current_code}) has a concurrent event between samples ({start}) and '
                               '({stop}). An additional stim channel will be used/created: ({channel}).'
                               .format(current_code=code, start=start, stop=stop,
                                       channel=stim_channel_names[channel_index]))

            stim_channels[channel_index][start:stop + 1] += code

        stim_info = mne.create_info(ch_names=stim_channel_names,
                                    sfreq=self.sampling_rate,
                                    ch_types='stim')

        stim_cnt = mne.io.RawArray(stim_channels, stim_info, verbose='WARNING')

        cnt = cnt.add_channels([stim_cnt])

        return cnt
