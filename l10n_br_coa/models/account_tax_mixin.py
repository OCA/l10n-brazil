# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountTaxMixin(models.AbstractModel):
    _name = 'account.tax.mixin'
    _description = 'Account Tax Mixin'

    deductible = fields.Boolean(
        string='Deductible Tax?',
        default=True,
    )
