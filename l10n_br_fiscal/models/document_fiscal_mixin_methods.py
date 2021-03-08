# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models

from ..constants.fiscal import (
    COMMENT_TYPE_FISCAL,
    COMMENT_TYPE_COMMERCIAL,
)


class FiscalDocumentMixinMethods(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin.methods'
    _description = 'Document Fiscal Mixin Methods'

    @api.multi
    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop('id', None)

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.multi
    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped('line_ids')

    @api.model
    def _get_amount_fields(self):
        """Get all fields with 'amount_' prefix"""
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()
        amount_fields = [f for f in fields if f.startswith('amount_')]
        return amount_fields

    def _compute_amount(self):
        fields = self._get_amount_fields()
        for doc in self:
            values = {key: 0.0 for key in fields}
            for line in doc._get_amount_lines():
                for field in fields:
                    if field in line._fields.keys():
                        values[field] += line[field]
                    if field.replace('amount_', '') in line._fields.keys():
                        values[field] += line[field.replace('amount_', '')]

                if line.fiscal_operation_line_id:
                    if line.fiscal_operation_line_id.add_to_amount and (
                            not line.cfop_id or line.cfop_id.finance_move):
                        values['amount_financial'] += line.amount_taxed

            doc.update(values)

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self,
        }

    def document_comment(self):
        for d in self:
            # Fiscal Comments
            fsc_comments = []
            fsc_comments.append(d.fiscal_additional_data or '')
            fsc_comments.append(d.comment_ids.filtered(
                lambda c: c.comment_type == COMMENT_TYPE_FISCAL
                ).compute_message(d._document_comment_vals()) or '')
            d.fiscal_additional_data = ', '.join(
                [c for c in fsc_comments if c])

            # Commercial Coments
            com_comments = []
            com_comments.append(d.customer_additional_data or '')
            com_comments.append(d.comment_ids.filtered(
                lambda c: c.comment_type == COMMENT_TYPE_COMMERCIAL
                ).compute_message(d._document_comment_vals()) or '')
            d.customer_additional_data = ', '.join(
                [c for c in com_comments if c])
            d.line_ids.document_comment()

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.operation_name = self.fiscal_operation_id.name
            self.comment_ids = self.fiscal_operation_id.comment_ids
