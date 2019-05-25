# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountTaxTemplate(models.Model):
    _name = 'account.tax.template'
    _inherit = ['account.tax.template', 'account.tax.fiscal.abstract']
