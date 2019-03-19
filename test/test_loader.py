# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_loader.py) is part of neurone_loader                        -
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
import numpy as np

try:
    # noinspection PyPackageRequirements
    import mock
except ImportError:
    import unittest.mock as mock

from neurone_loader.loader import Recording, Session

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')

try:
    FileNotFoundError
except NameError:
    # there is not FileNotFoundError in Python 2.7
    # noinspection PyShadowingBuiltins,PyPep8Naming
    FileNotFoundError = IOError


class TestDataParsing(TestCase):
    def setUp(self):
        self.container = Recording(data_path)
        self.time_length = reduce(lambda x, y: x + y,
                                  [p.time_stop - p.time_start
                                   for s in self.container.sessions
                                   for p in s.phases]).total_seconds()

    def test_data_shape(self):
        shape = self.container.data.shape

        channels = self.container.n_channels
        samples = self.container.n_samples
        self.assertEqual(shape, (samples, channels))

    def test_channel_length(self):
        self.assertEqual(len(self.container.channels),
                         self.container.n_channels)

    def test_sampling_rate(self):
        samples = self.container.n_samples
        sampling_rate = self.container.sampling_rate
        expected_length = float(samples) / float(sampling_rate)
        self.assertAlmostEqual(self.time_length, expected_length, places=0)

    def test_data_abs(self):
        uv_limit = 300
        maximum = np.argmax(self.container.data)
        self.assertLessEqual(uv_limit, maximum)

    def test_event_codes(self):
        events = self.container.events
        codes = np.unique(events['Code'].values)
        self.assertTrue((codes == self.container.event_codes).all())

    def test_data_and_event_ends(self):
        data_ends_within_seconds_after_last_event = 15

        events = self.container.events
        samples = self.container.n_samples
        last_event_stop_sample = events['StopSampleIndex'].values[-1]
        last_event_stop_seconds = events['StopTime'].values[-1]

        for a, b, d_max in [(last_event_stop_seconds, self.time_length,
                             data_ends_within_seconds_after_last_event),
                            (last_event_stop_sample, samples,
                             self.container.sampling_rate * data_ends_within_seconds_after_last_event)]:
            delta = np.abs(a - b)
            self.assertLessEqual(delta, d_max)

    def test_events_order(self):
        events = self.container.events
        event_start_samples = events['StartSampleIndex'].values.tolist()
        self.assertEqual(sorted(event_start_samples), event_start_samples)

    def tearDown(self):
        del self.container


class TestDataParsingSession(TestDataParsing):
    def setUp(self):
        self.container = Recording(data_path).sessions[0]
        self.time_length = reduce(lambda x, y: x + y,
                                  [p.time_stop - p.time_start
                                   for p in self.container.phases]).total_seconds()


class TestDataParsingPhase(TestDataParsing):
    def setUp(self):
        self.container = Recording(data_path).sessions[0].phases[0]
        self.time_length = (self.container.time_stop - self.container.time_start).total_seconds()


class TestContainerInitialisation(TestCase):
    def test_invalid_path(self):
        with self.assertRaises(AssertionError):
            Recording('../')

        with self.assertRaises(FileNotFoundError):
            Session('../')


class TestContainerHierarchy(TestCase):
    def setUp(self):
        self.rec = Recording(data_path)
        self.test_range = slice(20, 100)

    def test_modification_upwards_propagation(self):
        phase0 = self.rec.sessions[0].phases[0]
        phase_shape = phase0.data.shape
        test_shape = list(phase_shape)
        test_shape[0] = self.test_range.stop - self.test_range.start
        test_data = np.random.randint(0, 10000, test_shape)
        phase0.data[self.test_range] = test_data

        self.assertTrue((test_data == self.rec.sessions[0].data[self.test_range]).all())
        self.assertTrue((test_data == self.rec.data[self.test_range]).all())

    def test_modification_downwards_propagation(self):
        rec_shape = self.rec.data.shape
        test_shape = list(rec_shape)
        test_shape[0] = self.test_range.stop - self.test_range.start
        test_data = np.random.randint(0, 10000, test_shape)
        self.rec.data[self.test_range] = test_data

        self.assertTrue((test_data == self.rec.sessions[0].data[self.test_range]).all())
        self.assertTrue((test_data == self.rec.sessions[0].phases[0].data[self.test_range]).all())

    def tearDown(self):
        del self.rec


class TestChannelDroppingPhase(TestCase):
    class ChannelState:
        channel_count = None
        data = None
        mask = None

    def commonSetUp(self):
        self.container = Recording(data_path)
        self.invalid_channel = 'UnknownChannel'
        self.save_samples = 100

        index_one = np.random.randint(1, len(self.container.channels) - 1)
        index_two = np.random.randint(4, len(self.container.channels))
        while np.abs(index_one - index_two) < 3:
            index_two = np.random.randint(4, len(self.container.channels))

        self.valid_indexes = [index_one, index_one + 1, index_two]
        self.valid_channels = [self.container.channels[i] for i in self.valid_indexes]

        self.states = dict()

    def setUp(self):
        self.commonSetUp()
        self.container = self.container.sessions[0].phases[0]

    @mock.patch('logging.Logger.warning')
    def test_warning_recording(self, mocker):
        self.container.drop_channels([self.invalid_channel])
        self.assertIn(self.invalid_channel, mocker.call_args_list[0][0][0])  # channel name in warning message

    def save_state(self, container, state_name):
        state = self.ChannelState()
        state.channel_count = container.n_channels
        state.data = container.data[:self.save_samples].copy()
        state.mask = np.ones(state.data.shape[1], np.bool)
        for i in self.valid_indexes:
            state.mask[i] = False
        self.states[state_name] = state

    def check_state(self, container, state_name):
        state = self.states[state_name]

        self.assertEqual(state.channel_count - len(self.valid_channels), container.n_channels)
        self.assertTrue(set(self.valid_channels).isdisjoint(set(container.channels)))

        self.assertTrue(np.all(container.data[:self.save_samples] == state.data.T[state.mask].T))

    def do_drop(self):
        self.assertTrue(set(self.valid_channels).issubset(set(self.container.channels)))
        # drop oneplus in separate step to test dropping in sequence?
        self.container.drop_channels((self.valid_channels[0], self.valid_channels[2]))
        self.container.drop_channels((self.valid_channels[1],))

    def test_drop_before_loading(self):
        self.save_state(self.container, 'main_container')
        self.container.clear_data()
        self.assertFalse(self.container._has_data())
        self.do_drop()
        self.check_state(self.container, 'main_container')

    def test_drop_after_loading(self):
        self.container.preload()
        self.save_state(self.container, 'main_container')
        self.assertTrue(self.container._has_data())
        self.do_drop()
        self.check_state(self.container, 'main_container')

    def test_persistence(self):
        self.save_state(self.container, 'main_container')
        self.do_drop()
        self.container.clear_data()
        self.container.preload()
        self.check_state(self.container, 'main_container')

    def tearDown(self):
        del self.container


class TestChannelDroppingSession(TestChannelDroppingPhase):
    def setUp(self):
        self.commonSetUp()
        self.container = self.container.sessions[0]

    def test_persistence(self):
        # Also test change propagation to phase
        self.save_state(self.container.phases[0], 'phase0')
        TestChannelDroppingPhase.test_persistence(self)
        self.check_state(self.container.phases[0], 'phase0')

    def test_drop_before_loading(self):
        # Also test change propagation to phase
        self.save_state(self.container.phases[0], 'phase0')
        TestChannelDroppingPhase.test_drop_before_loading(self)
        self.check_state(self.container.phases[0], 'phase0')

    def test_drop_after_loading(self):
        # Also test change propagation to phase
        self.save_state(self.container.phases[0], 'phase0')
        TestChannelDroppingPhase.test_drop_after_loading(self)
        self.check_state(self.container.phases[0], 'phase0')


class TestChannelDroppingRecording(TestChannelDroppingPhase):
    def setUp(self):
        self.commonSetUp()

    def test_drop_before_loading(self):
        # Also test change propagation to session and phase
        self.save_state(self.container.sessions[0].phases[0], 'phase0')
        self.save_state(self.container.sessions[0], 'session0')
        TestChannelDroppingPhase.test_drop_before_loading(self)
        self.check_state(self.container.sessions[0].phases[0], 'phase0')
        self.check_state(self.container.sessions[0], 'session0')

    def test_drop_after_loading(self):
        # Also test change propagation to session and phase
        self.save_state(self.container.sessions[0].phases[0], 'phase0')
        self.save_state(self.container.sessions[0], 'session0')
        TestChannelDroppingPhase.test_drop_after_loading(self)
        self.check_state(self.container.sessions[0].phases[0], 'phase0')
        self.check_state(self.container.sessions[0], 'session0')

    def test_persistence(self):
        # Also test change propagation to session and phase
        self.save_state(self.container.sessions[0].phases[0], 'phase0')
        self.save_state(self.container.sessions[0], 'session0')
        TestChannelDroppingPhase.test_persistence(self)
        self.check_state(self.container.sessions[0].phases[0], 'phase0')
        self.check_state(self.container.sessions[0], 'session0')
