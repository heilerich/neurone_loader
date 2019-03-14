# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_utilities_neurone.py) is part of neurone_loader             -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from unittest import TestCase
from zodbpickle import pickle
import os
from hashlib import sha256
from multiprocessing import Pool
import numpy as np

from neurone_loader.neurone import *

data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
sessions = ['ses1', 'ses2']


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

    def test_empty_file(self):
        session_path = os.path.join(data_path, 'empty_session')
        events = read_neurone_events(session_path, sampling_rate=1)
        self.assertEqual(events, {'events': [], 'dtype': []})


class TestStability(TestCase):
    def test_event_stability(self):
        true_events = {
            'events': np.load(os.path.join(data_path, 'ses1_1_events.npy')),
            'dtype': np.dtype([('Revision', '<i4'), ('Type', '<i4'),
                               ('SourcePort', '<i4'), ('ChannelNumber', '<i4'),
                               ('Code', '<i4'), ('StartSampleIndex', '<i8'),
                               ('StopSampleIndex', '<i8'), ('DescriptionLength', '<i8'),
                               ('DescriptionOffset', '<i8'), ('DataLength', '<i8'),
                               ('DataOffset', '<i8'), ('StartTime', '<i8'),
                               ('StopTime', '<i8')])
        }

        read_events = read_neurone_events(os.path.join(data_path, sessions[0]))
        # noinspection PyUnresolvedReferences
        self.assertTrue((true_events['events'] == read_events['events']).all())
        self.assertEqual(true_events['dtype'], read_events['dtype'])
        self.assertEqual(true_events.keys(), read_events.keys())

    def test_protocol_stability(self):
        for session in sessions:
            with open(os.path.join(data_path, '{}_meta.pkl'.format(session)), 'rb') as f:
                true_session_meta = pickle.load(f)

            session_meta = read_neurone_protocol(os.path.join(data_path, session))
            self.assertEqual(true_session_meta, session_meta)

    def test_data_stability(self):
        hashes = {'ses1:1': '4c04a0071d7f0dfd6bd337bb5cabf7a33f6d3a5a57d93de1926c8d42fda2725b',
                  'ses1:2': '76b8fdf3f951c7b357a4a59c719669058925a432e7e7a6a749dcc64b13925086',
                  'ses1:3': 'c1782cecded74fb7567a9c9c159d33fbcbc67e9f0def4e3b27b0d2814d352ec9',
                  'ses1:4': 'fc29a8911987c6a7667539ebe547ff76bfd0eae7f29a49cdb8279d1d7f402876',
                  'ses2:1': '887012a3f8449a3dbe87cab0e7d8411ee1989cdffadf9b46ee05d7619bbaf593',
                  'ses2:2': '2dbede3c93f4b37112ebee9798d02937e85e3f31a3bcf3d987222fed67d09379',
                  'ses2:3': 'e019b3124a1b2f159283d897aca7b1821676a3c2d5e12dfb7ab0a2b8cac3f892',
                  'ses2:4': '4af04066ed8651c4cec352f23467258f4acb8091385af24bb43db18e9179dbaf'}

        pool = Pool()
        results = []

        for session in sessions:
            session_path = os.path.join(data_path, session)
            session_meta = read_neurone_protocol(session_path)
            phases = session_meta['phases'][:-1] if session == session[-1] else session_meta['phases']
            for phase in phases:
                number = phase['number']
                results.append(pool.apply_async(_hash_data,
                                                (session, session_path, number)))

            if session == sessions[-1]:
                key, shasum = _hash_data(session, session_path,
                                         session_meta['phases'][-1]['number'])
                self.assertEqual(hashes[key], shasum)

        for result in results:
            key, shasum = result.get(timeout=20)
            self.assertEqual(hashes[key], shasum)


def _hash_data(session, session_path, number):
    key = ':'.join([session, number])
    session_data = read_neurone_data(session_path, number)
    return key, sha256(session_data.tobytes()).hexdigest()
