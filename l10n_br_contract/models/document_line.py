# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DocumentLine(models.Model):
    _inherit = 'l10n_br_fiscal.document.line'

    contract_line_id = fields.Many2one(
        string='Contract Line',
        comodel_name='contract.line',
        ondelete='set null',
    )
