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

        # this will force to create a new fiscal document line:
        vals['fiscal_document_id'] = False

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

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

    @api.depends('line_ids.freight_value')
    def _compute_amount_freight(self):
        for record in self:
            record.amount_freight = sum(
                record.line_ids.mapped('freight_value'))

    @api.multi
    def _inverse_amount_freight(self):
        for record in self:
            if all(record.line_ids.mapped('freight_value')):
                amount_freight_old = sum(
                    record.line_ids.mapped('freight_value'))
                for line in record.line_ids[:-1]:
                    line.freight_value = record.amount_freight * (
                        line.freight_value / amount_freight_old)
                record.line_ids[-1] = record.amount_freight - sum(
                    line.freight_value for line in record.line_ids[:-1])
            else:
                amount_all = sum(line.fiscal_price * line.fiscal_quantity
                                 for line in record.line_ids)
                for line in record.line_ids[:-1]:
                    line.freight_value = record.amount_freight * (
                        line.fiscal_price * line.fiscal_quantity / amount_all)
                record.line_ids[-1] = record.amount_freight - sum(
                    line.freight_value for line in record.line_ids[:-1])
            for line in record.line_ids:
                line._onchange_fiscal_taxes()
