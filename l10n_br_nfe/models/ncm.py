# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Ncm(models.Model):
    _inherit = "l10n_br_fiscal.ncm"
    _nfe_search_keys = ["code_unmasked"]
