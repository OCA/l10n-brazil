# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    # Note: fiscal_tax_ids already exists in account.tax model from l10n_br_account
    # This file is kept for backward compatibility and to ensure the field exists
    # The field definition is already in account_tax.py, so this is just a placeholder
    # to maintain the inheritance chain if needed
