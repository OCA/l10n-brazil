# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from collections import OrderedDict
import logging
import time
from functools import wraps

_logger = logging.getLogger(__name__)

PROF_DATA = OrderedDict()


# Adapted of https://stackoverflow.com/questions/ \
# 3620943/measuring-elapsed-time-with-the-time-module?answertab=votes#tab-top


def profile(fn):
    @wraps(fn)
    def with_profiling(*args, **kwargs):
        start_time = time.time()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = [0, []]
        PROF_DATA[fn.__name__][0] += 1
        PROF_DATA[fn.__name__][1].append(elapsed_time)

        return ret

    return with_profiling


def log_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        avg_time = sum(data[1]) / len(data[1])
        _logger.info(
            "[TIME] %.3f \t [AVERAGE] %.3f \t "
            "[NUM OF CALLS] %d \t [METHOD] %s \t" % (
                max_time, avg_time, data[0], fname
            )
        )


def clear_prof_data():
    global PROF_DATA
    PROF_DATA = OrderedDict()
