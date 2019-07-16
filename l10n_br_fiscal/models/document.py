# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class Document(models.Model):
    _name = 'l10n_br_fiscal.document'
    _inherit = 'l10n_br_fiscal.document.abstract'
    _description = 'Fiscal Document'
