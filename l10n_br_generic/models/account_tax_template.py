# -*- coding: utf-8 -*-
# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class AccountTaxTemplate(models.Model):
    """ Add fields used to define some brazilian taxes """
    _inherit = 'account.tax.template'

    tax_discount = fields.Boolean(
        string='Discount this Tax in Prince',
        related='tax_group_id.tax_discount',
        help="Mark it for (ICMS, PIS e etc.).")

    domain = fields.Selection(
        related='tax_group_id.domain',
        string='Tax Domain')

    base_reduction = fields.Float(
        string='Redution',
        digits=(16, 4),
        default=0.00,
        required=True,
        help="Um percentual decimal em % entre 0-1.")

    amount_mva = fields.Float(
        string='MVA Percent',
        digits=(16, 4),
        default=0.00,
        required=True,
        help="Um percentual decimal em % entre 0-1.")
