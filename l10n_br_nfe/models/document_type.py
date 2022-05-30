# Copyright (C) 2022  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentType(models.Model):
    _inherit = "l10n_br_fiscal.document.type"
    _nfe_search_keys = ["code"]
