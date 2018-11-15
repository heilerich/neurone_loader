# ------------------------------------------------------------------------------
#  This file (test_utilities_neurone.py) is part of neurone_loader             -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2018 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from unittest import TestCase
import pickle
import os

from neurone_loader.neurone import *

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
sessions = ['ses1', 'ses2']


class TestReadMetadata(TestCase):
    def test_read_neurone_protocol(self):
        for session in sessions:
            with open(os.path.join(data_path, '{}_meta.pkl'.format(session)),
                      'rb') as f:
                true_session_meta = pickle.load(f)

            session_meta = read_neurone_protocol(os.path.join(data_path, session))
            self.assertEqual(true_session_meta, session_meta)


class TestDataReading(TestCase):
    def test_length(self):
        for session in sessions:
            session_path = os.path.join(data_path, session)
            session_meta = read_neurone_protocol(session_path)
            channels = session_meta['channels']
            sampling_rate = session_meta['meta']['sampling_rate']

            for phase in session_meta['phases']:
                number = phase['number']
                n_samples_from_info, n_channels_from_info \
                    = read_neurone_data_info(session_path, number)
                self.assertEqual(len(channels), n_channels_from_info)

                duration = phase['time_stop'] - phase['time_start']
                expected_samples = sampling_rate * duration.total_seconds()
                self.assertAlmostEqual(n_samples_from_info, expected_samples,
                                       delta=sampling_rate * 0.1)
