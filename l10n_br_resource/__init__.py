# -*- coding: utf-8 -*-
# Copyright 2016 KMEE - Hendrix Costa <hendrix.costa@kmee.com.br>
# Copyright 2017 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import models, wizard

import logging
from odoo import api, fields, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def create_national_calendar(cr, registry):
    """Generate """
    env = api.Environment(cr, SUPERUSER_ID, {})

    wizard_pybrasil = env['wizard.pybrasil.holiday.import'].create(
        {
            'start_date': fields.Date.today(),
            'interval_type': 'years',
            'interval_number': 1,
        }
    )
    wizard_pybrasil.holiday_import()
    _logger.info(
        """Create new Brazilian calendar.
        \n from {start_date} to {end_date} """.format(
            start_date=wizard_pybrasil.start_date,
            end_date=wizard_pybrasil.end_date
        ))
