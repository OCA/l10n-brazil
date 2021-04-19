# Copyright (C) 2021 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    tax_group_id = fields.Many2one(
        comodel_name='account.tax.group',
        string='Tax Group',
    )
