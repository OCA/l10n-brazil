# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    fiscal_name = fields.Text(related="name")
    fiscal_partner_id = fields.Many2one(related="partner_id")
    fiscal_company_id = fields.Many2one(related="company_id")
    fiscal_currency_id = fields.Many2one(related="currency_id")
    fiscal_product_id = fields.Many2one(related="product_id")
    fiscal_uom_id = fields.Many2one(related="uom_id")
    fiscal_quantity = fields.Float(related="quantity")
    fiscal_price_unit = fields.Float(related="price_unit")


    def modified(self, fnames, create=False, before=False):
        """
        Modifying a dummy fiscal document (no document_type_id) line should not recompute
        any account.move.line related to the same dummy fiscal document line.
        """
        filtered = self.filtered(
            lambda rec: isinstance(rec.id, models.NewId)
            or not rec.document_id  # document_id might exist and be computed later
            or rec.document_id.document_type_id
        )
        return super(FiscalDocumentLine, filtered).modified(fnames, create, before)

    def _modified_triggers(self, tree, create=False):
        """
        Modifying a dummy fiscal document (no document_type_id) line should not recompute
        any account.move.line related to the same dummy fiscal document line.
        """
        filtered = self.filtered(
            lambda rec: isinstance(rec.id, models.NewId)
            or not rec.document_id  # document_id might exist and be computed later
            or rec.document_id.document_type_id
        )
        return super(FiscalDocumentLine, filtered)._modified_triggers(tree, create)
