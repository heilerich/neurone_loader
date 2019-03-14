# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (util.py) is part of neurone_loader                               -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

import logging
import sys


def get_logger():
    """
    Get the default logger for this module and set default settings.

    :return: the logger
    :rtype: logging.Logger
    """
    lgr = logging.getLogger('neurone_loader')
    lgr.setLevel(logging.INFO)
    fmt = logging.Formatter(fmt='%(asctime)s [%(name)s.%(module)s]:%(levelname)s: %(message)s', datefmt='%I:%M:%S')
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.NOTSET)
    stdout_handler.setFormatter(fmt)
    lgr.addHandler(stdout_handler)
    return lgr


logger = get_logger()
