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
        pass

    @property
    @abc.abstractmethod
    def events(self):
        """
        :return: should contain the events as a DataFrame, required fields are `StartSampleIndex`, `StopSampleIndex`
        and `Code`. Additional fields are ignored.
        :rtype: pandas.DataFrame
        """
        pass

    @property
    @abc.abstractmethod
    def channels(self):
        """
        :return: should contain the names of channels, matching the sequence used in the data property
        :rtype: list[str]
        """
        pass

    @property
    @abc.abstractmethod
    def sampling_rate(self):
        """
        :return: should contain the used sampling rate
        :rtype: int
        """
        pass

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

    def to_mne(self):
        """
        Convert loaded data to a mne.io.RawArray
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

        stim_channel = np.zeros_like(cnt.get_data()[0])
        ssc = [(start, stop, code) for (start, stop, code)
               in events[['StartSampleIndex', 'StopSampleIndex', 'Code']].values]

        for start, stop, code in ssc:
            stim_channel[start:stop+1] += code

        stim_info = mne.create_info(ch_names=['STI 014'],
                                    sfreq=self.sampling_rate,
                                    ch_types='stim')

        stim_cnt = mne.io.RawArray([stim_channel], stim_info, verbose='WARNING')

        cnt = cnt.add_channels([stim_cnt])

        return cnt
