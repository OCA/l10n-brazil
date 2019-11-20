# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class NFe(models.Model):
    _name = 'l10n_br_nfe.document'
    _inherit = ['l10n_br_fiscal.document', 'l10n_br_fiscal.document.eletronic']
    _table = 'l10n_br_fiscal_document'
    _description = 'NFe'
