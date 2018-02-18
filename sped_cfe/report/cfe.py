# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging
from odoo import api
from odoo.addons.report_py3o.models.py3o_report import py3o_report_extender

_logger = logging.getLogger(__name__)

try:
    from satcomum.ersat import ChaveCFeSAT
except (ImportError, IOError) as err:
    _logger.debug(err)


@api.model
@py3o_report_extender('sped_cfe.action_report_sped_documento_cfe')
def report_sped_documento_cfe(session, local_context):
    data = {
        'ChaveCFeSAT': ChaveCFeSAT,
    }
    local_context.update(data)
