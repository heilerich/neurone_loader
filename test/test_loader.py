# ------------------------------------------------------------------------------
#  This file (test_loader.py) is part of neurone_loader                        -
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
import numpy as np

from neurone_loader.loader import Recording, Session

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')


class TestDataParsing(TestCase):
    def setUp(self):
        self.rec = Recording(data_path)
        self.time_length = reduce(lambda x, y: x + y,
                                  [p.time_stop - p.time_start
                                   for s in self.rec.sessions
                                   for p in s.phases]).total_seconds()

    def test_data_shape(self):
        shape = self.rec.data.shape

        channels = self.rec.n_channels
        samples = self.rec.n_samples
        self.assertEqual(shape, (samples, channels))

    def test_channel_length(self):
        self.assertEqual(len(self.rec.channels),
                         self.rec.n_channels)

    def test_sampling_rate(self):
        samples = self.rec.n_samples
        sampling_rate = self.rec.sampling_rate
        expected_length = samples / sampling_rate
        self.assertAlmostEqual(self.time_length, expected_length, places=0)

    def test_data_abs(self):
        uv_limit = 300
        maximum = np.argmax(self.rec.data)
        self.assertLessEqual(uv_limit, maximum)

    def test_event_codes(self):
        events = self.rec.events
        codes = np.unique(events['Code'].values)
        self.assertTrue((codes == self.rec.event_codes).all())

    def test_data_and_event_ends(self):
        events = self.rec.events
        samples = self.rec.n_samples
        last_event_stop_sample = events['StopSampleIndex'].values[-1]
        last_event_stop_seconds = events['StopTime'].values[-1]

        for a, b, d_max in [(last_event_stop_seconds, self.time_length, 10),
                            (last_event_stop_sample, samples, 5000 * 10)]:
            delta = np.abs(a - b)
            self.assertLessEqual(delta, d_max)

    def test_events_order(self):
        events = self.rec.events
        event_start_samples = events['StartSampleIndex'].values.tolist()
        self.assertEqual(sorted(event_start_samples), event_start_samples)

    def test_invalid_path(self):
        with self.assertRaises(AssertionError):
            Recording('../')

        with self.assertRaises(FileNotFoundError):
            Session('../')
