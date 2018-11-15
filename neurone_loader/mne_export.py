# This file is part of neurone_loader
# (https://www.github.com/heilerich/neurone_loader)
# Copyright © 2018 Felix Heilmeyer.
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
# Please see the file LICENSE for details.

import logging
import numpy as np

logger = logging.getLogger(__name__)


class MneExportable:
    def _import_mne(self):
        try:
            import mne
            self._mne = mne
            return True
        except ImportError:
            logger.error("To convert data to an MNE object you must install MNE" \
                         "and all its dependencies.")
            return False

    def to_mne(self):
        """
        Convert loaded NeurOne data to a mne.io.RawArray

        Returns:
           - the converted mne.io.RawArray
        """

        if not hasattr(self, '_mne'):
            if not self._import_mne():
                return
        mne = self._mne

        # data is µV samples x channels, mne needs V channels x samples
        data = (self.data / (1000 * 1000)).T
        events = self.events

        info = mne.create_info(ch_names = self.channels,
                               sfreq = self.sampling_rate,
                               ch_types='eeg')

        cnt = mne.io.RawArray(data, info)

        stim_channel = np.zeros_like(cnt.get_data()[0])
        ssc = [(start, stop, code) for (start, stop, code) in events[['StartSampleIndex', 'StopSampleIndex', 'Code']].values]

        for start, stop, code in ssc:
            stim_channel[start:stop+1] += code

        stim_info = mne.create_info(ch_names=['STI 014'],
                                    sfreq=self.sampling_rate,
                                    ch_types='stim')

        stim_cnt = mne.io.RawArray([stim_channel], stim_info, verbose='WARNING')

        cnt = cnt.add_channels([stim_cnt])

        return cnt