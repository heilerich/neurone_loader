# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_metadata.py) is part of neurone_loader             -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2021 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

import os
import datetime
import logging
import datetime
from unittest import TestCase

from neurone_loader.neurone import read_neurone_protocol, _convert_time
from neurone_loader.loader import Recording
from neurone_loader.util import logger

logger.setLevel(logging.ERROR)
data_path = os.getenv('TEST_DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data'))

class TestMetadataReading(TestCase):
    def test_subject_info(self):
        session_path = os.path.join(data_path, 'ses1')
        session_protocol = read_neurone_protocol(session_path)
        subject_info = session_protocol['meta']['subject']
        self.assertEqual(subject_info['id'], 'FeHeSEP1')
        self.assertEqual(subject_info['first_name'], 'Test')
        self.assertEqual(subject_info['last_name'], 'Subject')
        self.assertEqual(subject_info['date_of_birth'], datetime.datetime(1979, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=3600))))

        session_path = os.path.join(data_path, 'ses2')
        session_protocol = read_neurone_protocol(session_path)
        subject_info = session_protocol['meta']['subject']
        self.assertEqual(subject_info['id'], 'FeHeSEP1')
        self.assertIsNone(subject_info['first_name'])
        self.assertIsNone(subject_info['last_name'])

    def test_convert_time(self):
        fixtures = [
            ('1979-01-01T00:00:00+02:00', datetime.datetime(1979, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))),
            ('1979-01-01T00:00:00-02:00', datetime.datetime(1979, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=79200)))),
            ('1979-01-01T00:00:00.00-02:00', datetime.datetime(1979, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=79200)))),
            ('1979-01-01T00:00:00.00000000000000000-02:00', datetime.datetime(1979, 1, 1, 0, 0, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=79200)))),
            ('2015-11-26T13:01:15.32988', datetime.datetime(2015, 11, 26, 13, 1, 15, 329880))
        ]
        for test_str, expected_result in fixtures:
            self.assertEqual(_convert_time(test_str), expected_result)

class TestMetadataExport(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container = Recording(data_path)
        cls.substitution_code = 10

    @classmethod
    def tearDownClass(cls):
        del cls.container

    def tearDown(self):
        del self.cnt

    def test_ses1(self):
        phase0 = self.container.sessions[0].phases[0]
        self.cnt = phase0.to_mne(substitute_zero_events_with=self.substitution_code)
        subject_info = self.cnt.info['subject_info']
        self.assertEqual(subject_info['his_id'], 'FeHeSEP1')
        self.assertEqual(subject_info['first_name'], 'Test')
        self.assertEqual(subject_info['last_name'], 'Subject')
        self.assertEqual(subject_info['birthday'], (1979, 1, 1))

    def test_ses2(self):
        phase0 = self.container.sessions[1].phases[0]
        self.cnt = phase0.to_mne(substitute_zero_events_with=self.substitution_code)
        subject_info = self.cnt.info['subject_info']
        self.assertEqual(subject_info['his_id'], 'FeHeSEP1')
        self.assertIsNone(subject_info['first_name'])
        self.assertIsNone(subject_info['last_name'])
        self.assertEqual(subject_info['birthday'], (1979, 1, 1))
