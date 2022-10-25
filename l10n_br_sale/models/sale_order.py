# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from functools import partial

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang


class SaleOrder(models.Model):
    _name = "sale.order"
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

    discount_rate = fields.Float(
        string="Discount",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="sale_order_comment_rel",
        column1="sale_id",
        column2="comment_id",
        string="Comments",
    )

    amount_freight_value = fields.Monetary(
        inverse="_inverse_amount_freight",
    )

    amount_insurance_value = fields.Monetary(
        inverse="_inverse_amount_insurance",
    )

    amount_other_value = fields.Monetary(
        inverse="_inverse_amount_other",
    )

    operation_name = fields.Char(
        copy=False,
    )

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("order_line")

    @api.depends("order_line")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends("order_line.price_total")
    def _amount_all(self):
        """Compute the total amounts of the SO."""
        for order in self:
            order._compute_amount()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        order_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "form":

            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["order_line"]["views"]["form"]["arch"]

            sub_form_node = self.env["sale.order.line"].inject_fiscal_fields(
                sub_form_view
            )

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "sale.order.line", False
            )

            order_view["fields"]["order_line"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        return order_view

    @api.onchange("discount_rate")
    def onchange_discount_rate(self):
        for order in self:
            for line in order.order_line:
                if line.discount_fixed:
                    continue
                if self.env.user.has_group("l10n_br_sale.group_discount_per_value"):
                    line.discount_value = (line.product_uom_qty * line.price_unit) * (
                        order.discount_rate / 100
                    )
                    line._onchange_discount_value()
                else:
                    line.discount = order.discount_rate
                    line._onchange_discount_percent()

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        result = super()._onchange_fiscal_operation_id()
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id
        return result

    def _prepare_invoice(self):
        self.ensure_one()
        result = super()._prepare_invoice()
        result.update(self._prepare_br_fiscal_dict())

        document_type_id = self._context.get("document_type_id")

        if document_type_id:
            document_type = self.env["l10n_br_fiscal.document.type"].browse(
                document_type_id
            )
        else:
            document_type = self.company_id.document_type_id
            document_type_id = self.company_id.document_type_id.id

        if document_type:
            result["document_type_id"] = document_type_id
            document_serie = document_type.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if document_serie:
                result["document_serie_id"] = document_serie.id

        if self.fiscal_operation_id:
            if self.fiscal_operation_id.journal_id:
                result["journal_id"] = self.fiscal_operation_id.journal_id.id

        return result

    def _create_invoices(self, grouped=False, final=False, date=None):

        inv_ids = super()._create_invoices(grouped=grouped, final=final, date=date)

        # In brazilian localization we need to overwrite this method
        # because when there are a sale order line with different Document
        # Fiscal Type the method should be create invoices separated.
        document_type_list = []

        for invoice_id in inv_ids:
            invoice_created_by_super = invoice_id

            # Identify how many Document Types exist
            for inv_line in invoice_created_by_super.invoice_line_ids:

                if inv_line.display_type or not inv_line.fiscal_operation_line_id:
                    continue

                fiscal_document_type = (
                    inv_line.fiscal_operation_line_id.get_document_type(
                        inv_line.move_id.company_id
                    )
                )

                if fiscal_document_type.id not in document_type_list:
                    document_type_list.append(fiscal_document_type.id)

            # Check if there more than one Document Type
            if (
                fiscal_document_type.id != invoice_created_by_super.document_type_id.id
            ) or (len(document_type_list) > 1):

                # Remove the First Document Type,
                # already has Invoice created
                invoice_created_by_super.document_type_id = document_type_list.pop(0)

                for document_type in document_type_list:
                    document_type = self.env["l10n_br_fiscal.document.type"].browse(
                        document_type
                    )

                    inv_obj = self.env["account.move"]
                    invoices = {}
                    references = {}
                    invoices_origin = {}
                    invoices_name = {}

                    for order in self:
                        group_key = (
                            order.id
                            if grouped
                            else (order.partner_invoice_id.id, order.currency_id.id)
                        )

                        if group_key not in invoices:
                            inv_data = order.with_context(
                                document_type_id=document_type.id
                            )._prepare_invoice()
                            invoice = inv_obj.create(inv_data)
                            references[invoice] = order
                            invoices[group_key] = invoice
                            invoices_origin[group_key] = [invoice.invoice_origin]
                            invoices_name[group_key] = [invoice.name]
                            inv_ids = inv_ids + invoice
                        elif group_key in invoices:
                            if order.name not in invoices_origin[group_key]:
                                invoices_origin[group_key].append(order.name)
                            if (
                                order.client_order_ref
                                and order.client_order_ref
                                not in invoices_name[group_key]
                            ):
                                invoices_name[group_key].append(order.client_order_ref)

                    # Update Invoice Line
                    for inv_line in invoice_created_by_super.invoice_line_ids:
                        fiscal_document_type = (
                            inv_line.fiscal_operation_line_id.get_document_type(
                                inv_line.move_id.company_id
                            )
                        )
                        if fiscal_document_type.id == document_type.id:
                            copied_vals = inv_line.copy_data()[0]
                            copied_vals["move_id"] = invoice.id
                            copied_vals["recompute_tax_line"] = True
                            new_line = self.env["account.move.line"].new(copied_vals)
                            invoice.invoice_line_ids += new_line
                            order_line = self.order_line.filtered(
                                lambda x: x.invoice_lines in inv_line
                            )
                            if len(order_line.invoice_lines) > 1:
                                # TODO: É valido tratar isso no caso de já ter mais
                                #  faturas geradas e vinvuladas a linha
                                continue
                            else:
                                order_line.invoice_lines = invoice.invoice_line_ids
                            invoice_id.invoice_line_ids -= inv_line

            invoice_created_by_super.document_serie_id = (
                fiscal_document_type.get_document_serie(
                    invoice_created_by_super.company_id,
                    invoice_created_by_super.fiscal_operation_id,
                )
            )

        return inv_ids

    def _amount_by_group(self):
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
                        computed_tax.get("tax_value", 0.0), precision_rounding=pr
                    ):
                        group = tax.tax_group_id
                        res.setdefault(group, {"amount": 0.0, "base": 0.0})
                        res[group]["amount"] += computed_tax.get("tax_value", 0.0)
                        res[group]["base"] += computed_tax.get("base", 0.0)
            res = sorted(res.items(), key=lambda l: l[0].sequence)
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
