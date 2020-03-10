# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountTaxAbstract(models.AbstractModel):
    _name = "account.tax.fiscal.abstract"
    _description = "Account Tax Fiscal Abstract"
