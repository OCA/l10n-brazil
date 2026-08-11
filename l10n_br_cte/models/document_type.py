# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentType(models.Model):
    _inherit = "l10n_br_fiscal.document.type"
    _cte_search_keys = ["code"]
