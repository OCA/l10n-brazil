# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from functools import partial

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.purchase_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ("state", "=", "approved"),
            ("fiscal_type", "in", ("purchase", "other", "purchase_refund")),
        ]
        return domain

    active_company_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Active Company Country",
        default=lambda self: self.env.company.country_id,
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="purchase_order_comment_rel",
        column1="purchase_id",
        column2="comment_id",
        string="Comments",
        compute="_compute_comment_ids",
        store=True,
    )

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if self.env.company.country_id.code != "BR":
            return arch, view
        if view_type == "form" and self.env.company.country_id.code == "BR":
            arch = self.env["purchase.order.line"].inject_fiscal_fields(arch)

        if view_type == "form" and (
            self.env.user.has_group("l10n_br_purchase.group_line_fiscal_detail")
            or self.env.context.get("force_line_fiscal_detail")
        ):
            for sub_tree_node in arch.xpath("//field[@name='order_line']/list"):
                sub_tree_node.attrib["editable"] = ""

        return arch, view

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "order_line"

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super()._prepare_invoice()
        # Ensure the invoice partner is resolved via address_get.
        # The core _prepare_invoice uses address_get but in some
        # MRO configurations its result may not reach this override
        # (e.g. when purchase_stock or other modules reshape the
        #  method-resolution chain).  Mirror _get_fiscal_partner
        # below which already applies the same safeguard.
        partner_invoice = self.partner_id.address_get(["invoice"])["invoice"]
        invoice_vals["partner_id"] = partner_invoice
        if self.fiscal_operation_id:
            # O caso Brasil se caracteriza por ter a Operação Fiscal
            document_type_id = (
                self.order_line[0].fiscal_operation_line_id.document_type_id.id
                if self.order_line
                and self.order_line[0].fiscal_operation_line_id.document_type_id
                else (
                    self.fiscal_operation_id.document_type_ids[0].document_type_id.id
                    if self.fiscal_operation_id
                    and self.fiscal_operation_id.document_type_ids
                    else self.company_id.document_type_id.id
                )
            )
            invoice_vals.update(
                {
                    "ind_final": self.ind_final,
                    "fiscal_operation_id": self.fiscal_operation_id.id,
                    "document_type_id": document_type_id,
                }
            )
        return invoice_vals

    @api.depends(
        "order_line.fiscal_amount_untaxed",
        "order_line.fiscal_amount_tax",
        "order_line.fiscal_amount_total",
    )
    def _amount_all(self):
        """Override to use fiscal amounts directly for Brazilian POs.

        Odoo 18's _amount_all recomputes taxes via AccountTax utilities
        from the standard taxes_id field, ignoring Brazilian fiscal taxes.
        For POs with a fiscal operation, we override the computed amounts
        with the fiscal line totals instead, mirroring l10n_br_account's
        _compute_amount override on account.move.
        """
        result = super()._amount_all()
        for order in self.filtered("fiscal_operation_id"):
            lines = order.order_line
            order.amount_untaxed = sum(lines.mapped("fiscal_amount_untaxed"))
            order.amount_tax = sum(lines.mapped("fiscal_amount_tax"))
            order.amount_total = sum(lines.mapped("fiscal_amount_total"))
        return result

    def _amount_by_group(self):
        """Compute tax group totals from fiscal tax IDs.

        Mirror l10n_br_sale's approach: iterate over line.fiscal_tax_ids
        and group computed tax values by tax_group_id.
        """
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(
                formatLang,
                self.with_context(lang=order.partner_id.lang).env,
                currency_obj=currency,
            )
            res = {}
            for line in order.order_line:
                taxes = line._compute_taxes(line.fiscal_tax_ids)["taxes"]
                for tax in line.fiscal_tax_ids:
                    computed_tax = taxes.get(tax.tax_domain)
                    pr = order.currency_id.rounding
                    if computed_tax and not float_is_zero(
                        computed_tax.get("tax_value", 0.0),
                        precision_rounding=pr,
                    ):
                        group = tax.tax_group_id
                        res.setdefault(group, {"amount": 0.0, "base": 0.0})
                        res[group]["amount"] += computed_tax.get("tax_value", 0.0)
                        res[group]["base"] += computed_tax.get("base", 0.0)
            res = sorted(res.items(), key=lambda line: line[0].sequence)
            order.amount_by_group = [
                (
                    line[0].name,
                    line[1]["amount"],
                    line[1]["base"],
                    fmt(line[1]["amount"]),
                    fmt(line[1]["base"]),
                    len(res),
                )
                for line in res
            ]

    def _get_fiscal_partner(self):
        self.ensure_one()
        partner = super()._get_fiscal_partner()
        if partner.id != partner.address_get(["invoice"]).get("invoice"):
            partner = self.env["res.partner"].browse(
                partner.address_get(["invoice"]).get("invoice")
            )
        return partner
