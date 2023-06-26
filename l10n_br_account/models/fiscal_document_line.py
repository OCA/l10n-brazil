# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    # proxy fields to enable writing the related (shadowed) fields
    # to the fiscal doc line from the aml through the _inherits system
    # despite they have the same names.
    fiscal_name = fields.Text(related="name", readonly=False)
    fiscal_product_id = fields.Many2one(related="product_id", readonly=False)
    fiscal_uom_id = fields.Many2one(related="uom_id", readonly=False)
    fiscal_quantity = fields.Float(related="quantity", readonly=False)
    fiscal_price_unit = fields.Float(related="price_unit", readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        self.env.cr.execute(
            "alter table account_move_line alter column fiscal_document_Line_id drop not null;"
        )  # FIXME move to _auto_init
        records = []
        for values in vals_list:
            if values.get("document_id") and not isinstance(
                values.get("document_id"), models.NewId
            ):
                records.append(super().create(values))  # TODO repair batch create
        return records
