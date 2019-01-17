# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserWarning

MIS_REPORT_MODE = [
    ('contabil', u'Contábil'),
    ('gerencial', 'Gerencial'),
]


class MisReport(models.Model):

    _inherit = 'mis.report'

    report_mode = fields.Selection(
        string=u'Modalidade de relatório',
        selection=MIS_REPORT_MODE,
        default='contabil'
    )
    considerations = fields.Text(
        string=u'Considerações finais'
    )
