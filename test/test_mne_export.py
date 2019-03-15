# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_mne_export.py) is part of neurone_loader                    -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------
from unittest import TestCase
import os
from functools import reduce
# noinspection PyPackageRequirements
import mne
import numpy as np
import sys

# noinspection PyPackageRequirements
from braindecode.datasets.bbci import BBCIDataset

try:
    # noinspection PyPackageRequirements
    import mock
except ImportError:
    import unittest.mock as mock

from neurone_loader.loader import Recording, Session, Phase
from neurone_loader.mne_export import UnknownChannelException

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
bbci_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data', 'converted_1-1_250Hz.BBCI.mat')


class TestRecording(TestCase):
    @classmethod
    def _get_container(cls):
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

    @classmethod
    def tearDownClass(cls):
        del cls.container
        # noinspection PyUnresolvedReferences
        del cls.cnt

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
        event_codes = self.container.event_codes.tolist()  # type: list
        event_codes.remove(0)
        invalid_code = event_codes[0]

        with self.assertRaises(AssertionError):
            self.container.to_mne(substitute_zero_events_with=invalid_code)

        with self.assertRaises(AssertionError):
            # noinspection PyTypeChecker
            self.container.to_mne(substitute_zero_events_with='not_int')


class TestSession(TestRecording):
    @classmethod
    def _get_container(cls):
        recording = Recording(data_path)
        cls.container = Session(recording.sessions[0].path)

        cls.time_length = reduce(lambda x, y: x + y, [p.time_stop - p.time_start
                                                      for p in cls.container.phases]).total_seconds()


class TestPhase(TestRecording):
    @classmethod
    def _get_container(cls):
        recording = Recording(data_path)
        cls.container = Phase(recording.sessions[0].path, recording.sessions[0]._protocol['phases'][0])

        cls.time_length = (cls.container.time_stop - cls.container.time_start).total_seconds()


class TestMNEImport(TestCase):
    def test_import_failure(self):
        true_import = __import__

        def _import_mock(name, *args):
            if name == 'mne':
                raise ImportError
            else:
                return true_import(name, *args)

        builtin_name = 'builtins.__import__' if sys.version_info > (3, 0) else '__builtin__.__import__'

        with mock.patch(builtin_name, side_effect=_import_mock):
            container = Recording(data_path)
            with self.assertRaises(ImportError):
                container.to_mne()


class TestChannelMapping(TestCase):
    @classmethod
    def setUpClass(cls):
        uncommon_name = 'UncommonChannel'
        rec = Recording(data_path)
        phase = rec.sessions[0].phases[0]
        phase.channels[0] = uncommon_name

        cls.phase = phase
        cls.ch_name = uncommon_name

    @mock.patch('logging.Logger.warning')
    def test_unknown_name_mapping(self, mocker):
        cnt = self.phase.to_mne(substitute_zero_events_with=10, channel_type_mappings={'#unknown': 'misc'})
        self.assertEqual(cnt.ch_names[0], self.ch_name)
        self.assertEqual(mne.io.pick.channel_type(cnt.info, 0), 'misc')
        self.assertIn(self.ch_name, mocker.call_args_list[0][0][0])  # channel name in warning message

    def test_no_mapping(self):
        with self.assertRaises(UnknownChannelException):
            self.phase.to_mne(substitute_zero_events_with=10)

    def test_explicit_mapping(self):
        cnt = self.phase.to_mne(substitute_zero_events_with=10, channel_type_mappings={self.ch_name: 'misc'})
        self.assertEqual(cnt.ch_names[0], self.ch_name)
        self.assertEqual(mne.io.pick.channel_type(cnt.info, 0), 'misc')


class TestAgainstBBCI(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bbci_cnt = BBCIDataset(bbci_path).load()
        cls.bbci_events = mne.find_events(cls.bbci_cnt)

        raw_rec = Recording(data_path)
        cls.raw_phase = raw_rec.sessions[0].phases[0]
        cls.raw_cnt = cls.raw_phase.to_mne(substitute_zero_events_with=256).resample(cls.bbci_cnt.info['sfreq'])

        channel_indices_by_type = mne.io.pick.channel_indices_by_type(cls.raw_cnt.info)
        stim_channels = np.array(cls.raw_cnt.ch_names)[channel_indices_by_type['stim']].tolist()
        cls.raw_events = mne.find_events(cls.raw_cnt, stim_channels)

    def test_events(self):
        raw_events_concat = [self.raw_events[0]]
        for sample, _, code in self.raw_events[1:]:
            if -2 <= raw_events_concat[-1][0] - sample <= 2:
                raw_events_concat[-1][2] += code
            else:
                raw_events_concat.append([sample, 0, code])
        raw_events_concat = np.array(raw_events_concat)

        for ((b_sample, b_bf, b_code), (r_sample, r_bf, r_code)) in zip(raw_events_concat, self.bbci_events):
            self.assertAlmostEqual(r_sample, b_sample, delta=1)
            self.assertEqual(b_bf, r_bf)
            self.assertEqual(b_code, r_code)

    def test_length(self):
        self.assertEqual(self.bbci_cnt.last_samp, self.raw_cnt.last_samp)

        time_length = (self.raw_phase.time_stop - self.raw_phase.time_start).total_seconds()
        cnt_length = len(self.raw_cnt) / self.raw_cnt.info['sfreq']
        bbci_length = len(self.bbci_cnt) / self.bbci_cnt.info['sfreq']

        self.assertAlmostEqual(time_length, cnt_length, places=1)
        self.assertAlmostEqual(time_length, bbci_length, places=1)
        self.assertAlmostEqual(cnt_length, bbci_length, places=1)

    def test_data(self):
        raw_data = self.raw_cnt.pick_types(eeg=True).get_data()
        bbci_data = self.bbci_cnt.drop_channels(['STI 014']).get_data()
        self.assertEqual(raw_data.shape, bbci_data.shape)

        # bbci_data is in µV
        # difference per sample relative to average per sample
        rel_diff = (raw_data * 1e6 - bbci_data) / np.mean(np.stack([raw_data, bbci_data]), axis=0)

        # check that not more than 3% of samples differ more than 1% from average for sample
        percentage = np.sum(np.abs(rel_diff) > 1) / len(rel_diff.flatten())
        self.assertLess(percentage, 0.03)

    # noinspection PyUnresolvedReferences
    @classmethod
    def tearDownClass(cls):
        del cls.bbci_cnt
        del cls.raw_phase
        del cls.raw_cnt
