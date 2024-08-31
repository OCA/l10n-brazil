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

    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        related="account_line_ids.product_uom_id",
        store=True,
        string="UOM",
    )

    # proxy fields to enable writing the related (shadowed) fields
    # to the fiscal doc line from the aml through the _inherits system
    # despite they have the same names.
    fiscal_proxy_name = fields.Text(
        string="Fiscal Name",
        related="name",
        readonly=False,
    )
    fiscal_proxy_product_id = fields.Many2one(
        string="Fiscal Product",
        related="product_id",
        readonly=False,
    )
    fiscal_proxy_quantity = fields.Float(
        string="Fiscal Quantity",
        related="quantity",
        readonly=False,
    )
    fiscal_proxy_price_unit = fields.Float(
        string="Fiscal Price Unit",
        related="price_unit",
        readonly=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to ensure it filters out account.move.line records
        that lack a valid document_id or fiscal_operation_line_id. Prevent the
        creation  of fiscal document lines without these mandatory fields to avoid
        system crashes due to invalid records. If the conditions are not met, return an
        empty list instead of creating any records. This supports the creation of
        account.move.line records with NULL values for fiscal_document_line_id where
        necessary.
        """

        if self._context.get("create_from_move_line"):
            # Filter out the dictionaries that do not meet the conditions
            filtered_vals_list = [
                vals
                for vals in vals_list
                if vals.get("document_id") and vals.get("fiscal_operation_line_id")
            ]
            # Stop execution and return empty if no dictionary meets the conditions
            if not filtered_vals_list:
                return []
            # Assign the filtered list back to the original list for further processing
            vals_list = filtered_vals_list

        return super().create(vals_list)

    def _update_cache(self, values, validate=True):
        """
        Overriden to avoid raising error with ensure_one() in super()
        when called from some account.move.line onchange
        as we allow empty fiscal document line in account.move.line.
        """
        if len(self) == 0:
            return
        return super()._update_cache(values, validate)
