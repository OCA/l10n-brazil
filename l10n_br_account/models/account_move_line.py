# Copyright (C) 2016-TODAY Akretion <http://www.akretion.com>
#   @author Magno Costa <magno.costa@akretion.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = 'date_maturity, date desc, id desc'

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        related='invoice_id.fiscal_document_id',
        store=True,
    )

