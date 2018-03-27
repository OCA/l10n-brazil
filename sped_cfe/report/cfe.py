# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging
from odoo import api
from odoo.addons.report_py3o.models.py3o_report import py3o_report_extender
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)

try:
    from satcomum.ersat import ChaveCFeSAT, meio_pagamento
except (ImportError, IOError) as err:
    _logger.debug(err)


def formata_data(doc, data):	
    return Datetime.context_timestamp(doc, Datetime.from_string(data))


@api.model
@py3o_report_extender('sped_cfe.action_report_sped_documento_cfe')
def report_sped_documento_cfe(session, local_context):
    data = {
        'ChaveCFeSAT': ChaveCFeSAT,
        'meio_pagamento': meio_pagamento,
        'formata_data': formata_data,
    }
    local_context.update(data)

import odoo
from odoo.report.interface import report_int


class report_custom(report_int):
    '''
        Custom report for return danfe
    '''

    def create(self, cr, uid, ids, datas, context=None):
        if not context:
            context = dict()
        env = odoo.api.Environment(cr, uid, context)
        datas['ids'] = ids
        records = env['sped.documento'].browse(ids)
        pdf = records.gera_pdf()
        return pdf, 'pdf'

report_custom('report.report_sped_documento_cfe')
