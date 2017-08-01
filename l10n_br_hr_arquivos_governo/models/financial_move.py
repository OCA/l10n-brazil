# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from openerp import fields, models

_logger = logging.getLogger(__name__)


class FinancialMove(models.Model):
    _inherit = b'financial.move'

    sefip_id = fields.Many2one(
        comodel_name='l10n_br.hr.sefip',
        string='Sefip',
    )
