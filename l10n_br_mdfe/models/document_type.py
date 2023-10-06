# Copyright (C) 2023 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentType(models.Model):
    _inherit = "l10n_br_fiscal.document.type"
    _mdfe_search_keys = ["code"]
