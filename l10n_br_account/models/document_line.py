# Copyright (C) 2021 - TODAY Gabriel Cardoso de Faria - Kmee
# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import float_compare


class FiscalDocumentLine(models.Model):
    _inherit = "l10n_br_fiscal.document.line"

    account_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="fiscal_document_line_id",
        string="Invoice Lines",
    )

    uom_id = fields.Many2one(
        compute="_compute_product_uom_id",
        store=True,
        readonly=False,
        precompute=True,
        ondelete="restrict",
    )

    # -------------------------------------------------------------------------
    # SHADOWED FIELDS SYNC
    # -------------------------------------------------------------------------

    product_id = fields.Many2one(inverse="_inverse_product_id")
    name = fields.Char(inverse="_inverse_name")
    quantity = fields.Float(inverse="_inverse_quantity")
    price_unit = fields.Float(inverse="_inverse_price_unit")

    @api.onchange("product_id")
    def _inverse_product_id(self):
        for line in self:
            for aml in line.account_line_ids:
                if aml.product_id != line.product_id:
                    aml.product_id = line.product_id.id

    @api.onchange("name")
    def _inverse_name(self):
        for line in self:
            for aml in line.account_line_ids:
                if aml.name != line.name:
                    aml.name = line.name

    @api.onchange("quantity")
    def _inverse_quantity(self):
        for line in self:
            for aml in line.account_line_ids:
                if (
                    float_compare(
                        aml.quantity,
                        line.quantity,
                        self.env["decimal.precision"].precision_get(
                            "Product Unit of Measure"
                        ),
                    )
                    != 0
                ):
                    aml.quantity = line.quantity

    @api.onchange("price_unit")
    def _inverse_price_unit(self):
        for line in self:
            for aml in line.account_line_ids:
                if (
                    aml.currency_id.compare_amounts(aml.price_unit, line.price_unit)
                    != 0
                ):
                    aml.price_unit = line.price_unit

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for line in self:
            # vendor bills should have the product purchase UOM
            if line.fiscal_operation_type == "in":
                line.uom_id = line.product_id.uom_po_id
            else:
                line.uom_id = line.product_id.uom_id

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

        if self._context.get("create_from_account"):
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
