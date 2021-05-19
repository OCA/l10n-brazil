# Copyright (C) 2020 - TODAY Renato Lima - Akretion
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class AccountTax(models.Model):
    _name = 'account.tax'
    _inherit = ['account.tax.mixin', 'account.tax']
