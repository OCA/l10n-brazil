# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class TaxIpiGuideline(models.Model):
    _inherit = "l10n_br_fiscal.tax.ipi.guideline"
    _nfe_search_keys = ["code_unmasked"]
