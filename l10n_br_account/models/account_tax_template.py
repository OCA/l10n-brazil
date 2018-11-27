# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields
from odoo.addons import decimal_precision as dp


class AccountTaxTemplate(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax.template'

    domain = fields.Selection(
        related='tax_group_id.domain',
        string='Tax Domain')

    tax_discount = fields.Boolean(
        string='Discount this Tax in Prince',
        help="Mark it for (ICMS, PIS e etc.).",
        related='tax_group_id.tax_discount')

    base_reduction = fields.Float(
        string='Redution', required=True,
        digits_compute=dp.get_precision('Account'),
        help="Um percentual decimal em % entre 0-1.",
        default=0.00)

    amount_mva = fields.Float(
        string='MVA Percent', required=True,
        digits_compute=dp.get_precision('Account'),
        help="Um percentual decimal em % entre 0-1.",
        default=0.00)

    amount_type = fields.Selection(
        add_selection=[('quantity', 'Quantity')])
