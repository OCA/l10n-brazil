# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleBlanketOrder(models.Model):
    _name = "sale.blanket.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.sale_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.company.copy_note

    @api.model
    def _fiscal_operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    ind_pres = fields.Selection(
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    copy_note = fields.Boolean(
        string="Copy Sale note on invoice",
        default=_default_copy_note,
    )

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related="partner_id.cnpj_cpf",
    )

    legal_name = fields.Char(
        string="Legal Name",
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="State Tax Number/RG",
        related="partner_id.inscr_est",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_blanket_order_comment_rel",
        column1="sale_blanket_order_id",
        column2="comment_id",
        string="Comments",
    )

    operation_name = fields.Char(
        copy=False,
    )

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("line_ids")

    @api.depends("line_ids")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends("line_ids.price_total")
    def _amount_all(self):
        """Compute the total amounts of the Sale Blanket Order"""
        for order in self:
            order._compute_amount()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        order_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "form":
            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["line_ids"]["views"]["form"]["arch"]

            sub_form_node = self.env["sale.blanket.order.line"].inject_fiscal_fields(
                sub_form_view
            )

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "sale.blanket.order.line", False
            )

            order_view["fields"]["line_ids"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        return order_view

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        result = super()._onchange_fiscal_operation_id()
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id
        return result
