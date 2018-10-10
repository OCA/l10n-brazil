# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class AccountTaxTemplate(models.Model):
    """Implement computation method in taxes"""
    _inherit = 'account.tax.template'

    domain = fields.Selection(
        related='tax_group_id.domain',
        string='Tax Domain')
