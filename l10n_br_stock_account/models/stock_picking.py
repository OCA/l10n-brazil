# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        company = self.env.company
        fiscal_operation = False
        if self.env.company.country_id == self.env.ref("base.br"):
            fiscal_operation = company.stock_fiscal_operation_id
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
        return super()._compute_amount()

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

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        package = super()._put_in_pack(move_line_ids, create_package_level)
        if (
            package
            and self.picking_type_id.pre_generate_fiscal_document_number == "pack"
        ):
            self._generate_document_number()
        return package

    def button_validate(self):
        result = super().button_validate()
        for record in self:
            if (
                record.state == "done"
                and record.picking_type_id.pre_generate_fiscal_document_number
                == "validate"
            ):
                record._generate_document_number()
        return result

    def _generate_document_number(self):
        if self.company_id.document_type_id and self.fiscal_operation_id:
            if self.document_serie and self.document_number:
                return
            self.document_type_id = self.company_id.document_type_id
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            self.document_serie = self.document_serie_id.code
            self.document_number = self.document_serie_id.next_seq_number()
