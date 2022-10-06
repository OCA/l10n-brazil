# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        company = self.env.user.company_id
        fiscal_operation = self.env.user.company_id.stock_fiscal_operation_id
        picking_type_id = self.env.context.get("default_picking_type_id")
        if picking_type_id:
            picking_type = self.env["stock.picking.type"].browse(picking_type_id)
            fiscal_operation = picking_type.fiscal_operation_id or (
                company.stock_in_fiscal_operation_id
                if picking_type.code == "incoming"
                else company.stock_out_fiscal_operation_id
            )
        return fiscal_operation

    @api.model
    def _fiscal_operation_domain(self):
        # TODO Check in context to define in or out move default.
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    operation_name = fields.Char(
        string="Operation Name",
        copy=False,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="stock_picking_comment_rel",
        column1="picking_id",
        column2="comment_id",
        string="Comments",
    )

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("move_lines")

    @api.depends("move_lines")
    def _compute_amount(self):
        super()._compute_amount()

    @api.depends("move_lines.price_unit")
    def _amount_all(self):
        """Compute the total amounts of the Picking."""
        for picking in self:
            picking._compute_amount()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        order_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "form":

            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["move_ids_without_package"]["views"][
                "form"
            ]["arch"]

            sub_form_node = self.env["stock.move"].inject_fiscal_fields(sub_form_view)

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "stock.move", None
            )

            order_view["fields"]["move_ids_without_package"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        return order_view
