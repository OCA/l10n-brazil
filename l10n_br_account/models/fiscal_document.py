# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2020 - TODAY Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    SITUACAO_EDOC_EM_DIGITACAO,
)


class FiscalDocument(models.Model):
    _inherit = 'l10n_br_fiscal.document'

 @api.depends('line_ids')
    def _compute_move_template_ids(self):
        for record in self:
            record.move_template_ids = record.line_ids.mapped('move_template_id')

    move_template_ids = fields.Many2many(
        comodel_name='l10n_br_account.move.template',
        compute='_compute_move_template_ids',
        readonly=True,
    )

    @api.multi
    def unlink(self):
        draft_documents = self.filtered(
            lambda d: d.state == SITUACAO_EDOC_EM_DIGITACAO)

        if draft_documents:
            UserError(_("You cannot delete a fiscal document "
                        "which is not draft state."))

        invoices = self.env['account.invoice'].search(
            [('fiscal_document_id', 'in', self.ids)])
        invoices.unlink()
        return super().unlink()

