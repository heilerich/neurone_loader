# ------------------------------------------------------------------------------
#  This file (test_mne_export.py) is part of neurone_loader                    -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2018 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from unittest import TestCase
import os
from functools import reduce
import mne
import numpy as np

from neurone_loader.loader import Recording, Session, Phase

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
sessions = ['ses1', 'ses2']


class TestAgainstConvertedBBCI(TestCase):
    pass


class TestRecording(TestCase):
    @classmethod
    def _get_container(cls):
        # override self.container, self.time_length according to session/phase/recording
        cls.container = Recording(data_path)
        cls.time_length = reduce(lambda x, y: x + y, [p.time_stop - p.time_start
                                                      for s in cls.container.sessions
                                                      for p in s.phases]).total_seconds()

    @classmethod
    def setUpClass(cls):
        cls._get_container()
        cls.substitution_code = 10
        # noinspection PyUnresolvedReferences
        cls.cnt = cls.container.to_mne(substitute_zero_events_with=cls.substitution_code)

        channel_indices_by_type = mne.io.pick.channel_indices_by_type(cls.cnt.info)
        stim_channels = np.array(cls.cnt.ch_names)[channel_indices_by_type['stim']].tolist()
        cls.cnt_events = mne.find_events(cls.cnt, stim_channels)

    def test_time_length(self):
        cnt_time_length = self.cnt.last_samp / self.cnt.info['sfreq']
        self.assertAlmostEqual(cnt_time_length, self.time_length, delta=2)

    def test_event_count(self):
        self.assertEqual(len(self.container.events), len(self.cnt_events))

    def test_event_codes(self):
        cnt_codes = set(np.unique(self.cnt_events.T[2]))
        container_codes = set(self.container.event_codes)
        container_codes.remove(0)
        container_codes.add(self.substitution_code)
        self.assertEqual(container_codes, cnt_codes)

    def test_conversion_without_zero_substitution(self):
        with self.assertRaises(AssertionError):
            self.container.to_mne()

    def test_invalid_substitution(self):
        event_codes = self.container.event_codes.tolist()
        event_codes.remove(0)
        invalid_code = event_codes[0]

        with self.assertRaises(AssertionError):
            self.container.to_mne(substitute_zero_events_with=invalid_code)

        with self.assertRaises(AssertionError):
            self.container.to_mne(substitute_zero_events_with='not_int')

# Subclass with phase, session, recording?
