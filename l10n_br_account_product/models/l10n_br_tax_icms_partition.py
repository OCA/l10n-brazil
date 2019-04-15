# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrTaxIcmsPartition(models.Model):

    _name = 'l10n_br_tax.icms_partition'
    _description = 'Icms Partition'

    date_start = fields.Date(
        string=u'Data Inicial',
        required=True)

    date_end = fields.Date(
        string=u'Data Final',
        required=True)

    rate = fields.Float(
        string=u'Percentual Interestadual de Rateio',
        required=True)
