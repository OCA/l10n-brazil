# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from ..constants.icms import ICMS_BASE_TYPE, ICMS_BASE_TYPE_DEFAULT


class DocumentLine(models.Model):
    _name = "l10n_br_fiscal.document.line"
    _inherit = "l10n_br_fiscal.document.line.abstract"
    _description = "Fiscal Document Line"

    @api.model
    def _default_operation(self):
        # TODO add in res.company default Operation?
        return self.env['l10n_br_fiscal.operation']

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="l10n_br_fiscal_document_line_comment_rel",
        column1="document_line_id",
        column2="comment_id",
        string="Comments"
    )

    processed_comments = fields.Text(string="Processed Comments")

    operation_id = fields.Many2one(
        default=_default_operation,
        domain=lambda self: self._operation_domain())

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Document")

    icms_base_type = fields.Selection(
        selection=ICMS_BASE_TYPE,
        string="ICMS Base Type",
        default=ICMS_BASE_TYPE_DEFAULT)

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self.document_id,
            'item': self,
        }

    def document_comment(self):
        for record in self.filtered('comment_ids'):
            record.processed_comments = record.processed_comments and \
                                        record.processed_comments + ' - ' or ''
            record.processed_comments += record.comment_ids.compute_message(
                record._document_comment_vals())
