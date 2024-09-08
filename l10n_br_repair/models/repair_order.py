# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class RepairOrder(models.Model):
    _name = "repair.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.repair_fiscal_operation_id

    @api.model
    def _default_copy_note(self):
        return self.env.company.copy_repair_quotation_notes

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

    copy_repair_quotation_notes = fields.Boolean(
        string="Copiar Observação no documentos fiscal",
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

    fiscal_document_count = fields.Integer(
        string="Fiscal Document Count",
        related="invoice_count",
        readonly=True,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="repair_order_comment_rel",
        column1="repair_id",
        column2="comment_id",
        string="Comments",
    )

    invoice_count = fields.Integer(compute="_compute_get_invoiced", readonly=True)

    invoice_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_get_invoiced",
        readonly=True,
        copy=False,
    )

    # TODO: remover
    client_order_ref = fields.Char(string="Customer Reference", copy=False)

    operation_name = fields.Char(
        copy=False,
    )

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        lines = []
        lines += [lin for lin in self.mapped("operations")]
        lines += [lin for lin in self.mapped("fees_lines")]
        return lines

    def _get_product_amount_lines(self):
        """Get object lines instaces used to compute fields"""

        return self._get_amount_lines()

    @api.depends("operations", "fees_lines")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends(
        "operations.price_subtotal",
        "invoice_method",
        "fees_lines.price_subtotal",
        "pricelist_id.currency_id",
    )
    def _amount_untaxed(self):
        self._compute_amount()

    @api.depends(
        "operations.price_unit",
        "operations.product_uom_qty",
        "operations.product_id",
        "fees_lines.price_unit",
        "fees_lines.product_uom_qty",
        "fees_lines.product_id",
        "pricelist_id.currency_id",
        "partner_id",
    )
    def _amount_tax(self):
        self._compute_amount()

    @api.depends("amount_untaxed", "amount_tax")
    def _amount_total(self):
        self._compute_amount()

    @api.depends("state", "operations.invoice_line_id", "fees_lines.invoice_line_id")
    def _compute_get_invoiced(self):
        for order in self:
            invoice_ids = order.operations.mapped("invoice_line_id").mapped(
                "move_id"
            ).filtered(
                lambda r: r.move_type in ["out_invoice", "out_refund"]
            ) + order.fees_lines.mapped("invoice_line_id").mapped("move_id").filtered(
                lambda r: r.move_type in ["out_invoice", "out_refund"]
            )
            # Search for invoices which have been
            # 'cancelled' (filter_refund = 'modify' in account.move.refund')
            # use like as origin may contains multiple
            # references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search(
                [
                    ("invoice_origin", "like", order.name),
                    ("company_id", "=", order.company_id.id),
                    ("move_type", "in", ("out_invoice", "out_refund")),
                ]
            )

            invoice_ids |= refunds.filtered(
                lambda r, order=order: order.name
                in [
                    invoice_origin.strip()
                    for invoice_origin in r.invoice_origin.split(",")
                ]
            )

            # Search for refunds as well
            domain_inv = expression.OR(
                [
                    [
                        "&",
                        ("invoice_origin", "=", inv.name),
                        ("journal_id", "=", inv.journal_id.id),
                    ]
                    for inv in invoice_ids
                    if inv.name
                ]
            )

            if domain_inv:
                refund_ids = self.env["account.move"].search(
                    expression.AND(
                        [
                            [
                                "&",
                                ("move_type", "=", "out_refund"),
                                ("invoice_origin", "!=", False),
                            ],
                            domain_inv,
                        ]
                    )
                )
            else:
                refund_ids = self.env["account.move"].browse()

            order.update(
                {
                    "invoice_count": len(set(invoice_ids.ids + refund_ids.ids)),
                    "invoice_ids": invoice_ids.ids + refund_ids.ids,
                }
            )

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        order_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "form":
            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["operations"]["views"]["form"]["arch"]

            sub_form_node = self.env["repair.line"].inject_fiscal_fields(sub_form_view)

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "repair.line", False
            )

            order_view["fields"]["operations"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        if view_type == "form":
            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["fees_lines"]["views"]["form"]["arch"]

            sub_form_node = self.env["repair.fee"].inject_fiscal_fields(sub_form_view)

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "repair.fee", False
            )

            order_view["fields"]["fees_lines"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        return order_view

    def action_created_invoice(self):
        self.ensure_one()
        action = super().action_created_invoice()
        invoice_ids = self.mapped("invoice_ids").ids
        if self.invoice_count > 1:
            del action["view_id"]
            action["view_mode"] = "tree,form"
            action["domain"] = [("id", "in", invoice_ids)]
        return action

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a repair order.
        This method may be overridden to implement custom invoice generation
        (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()

        partner_invoice = self.partner_invoice_id or self.partner_id
        if not partner_invoice:
            raise UserError(
                _("You have to select an invoice address in the repair form.")
            )

        narration = self.quotation_notes
        currency = self.pricelist_id.currency_id
        company = self.env.company

        journal = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            ._get_default_journal()
        )
        if not journal:
            raise UserError(
                _(
                    "Please define an accounting sales journal for the company {} ({})."
                ).format(self.company_id.name, self.company_id.id)
            )

        fpos = self.env["account.fiscal.position"].get_fiscal_position(
            partner_invoice.id, delivery_id=self.address_id.id
        )

        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner_invoice.id,
            "partner_shipping_id": self.address_id.id,
            "currency_id": currency.id,
            "narration": narration,
            "invoice_origin": self.name,
            "repair_ids": [(4, self.id)],
            "invoice_line_ids": [],
            "fiscal_position_id": fpos.id,
            "company_id": company.id,
        }

        if partner_invoice.property_payment_term_id:
            invoice_vals[
                "invoice_payment_term_id"
            ] = partner_invoice.property_payment_term_id.id

        invoice_vals.update(self._prepare_br_fiscal_dict())

        document_type_id = self._context.get("document_type_id")

        if document_type_id:
            document_type = self.env["l10n_br_fiscal.document.type"].browse(
                document_type_id
            )
        else:
            document_type = self.company_id.document_type_id
            document_type_id = self.company_id.document_type_id.id

        if document_type:
            invoice_vals["document_type_id"] = document_type_id
            document_serie = document_type.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )
            if document_serie:
                invoice_vals["document_serie_id"] = document_serie.id

        if self.fiscal_operation_id:
            if self.fiscal_operation_id.journal_id:
                invoice_vals["journal_id"] = self.fiscal_operation_id.journal_id.id

        return invoice_vals

    def _create_invoices(self, group=False):
        """Creates invoice(s) for repair order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        grouped_invoices_vals = {}
        repairs = self.filtered(
            lambda repair: repair.state not in ("draft", "cancel")
            and not repair.invoice_id
            and repair.invoice_method != "none"
        )
        for repair in repairs:
            repair = repair.with_company(repair.company_id)

            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(
                    _("You have to select an invoice address in the repair form.")
                )

            narration = repair.quotation_notes
            currency = repair.pricelist_id.currency_id
            company = repair.env.company

            if (
                partner_invoice.id,
                currency.id,
                company.id,
            ) not in grouped_invoices_vals:
                grouped_invoices_vals[
                    (partner_invoice.id, currency.id, company.id)
                ] = []
            current_invoices_list = grouped_invoices_vals[
                (partner_invoice.id, currency.id, company.id)
            ]

            invoice_vals = repair._prepare_invoice()

            if not group or len(current_invoices_list) == 0:
                current_invoices_list.append(invoice_vals)
            else:
                invoice_vals["invoice_origin"] += ", " + repair.name
                invoice_vals["repair_ids"].append((4, repair.id))
                if not invoice_vals["narration"]:
                    invoice_vals["narration"] = narration
                else:
                    invoice_vals["narration"] += "\n" + narration

            # Create invoice lines from operations.
            for operation in repair.operations.filtered(lambda op: op.type == "add"):
                invoice_line_vals = operation._prepare_invoice_line()
                if group:
                    invoice_line_vals["name"] = repair.name + "-" + operation.name
                if currency == company.currency_id:
                    balance = -(operation.product_uom_qty * operation.price_unit)
                    invoice_line_vals.update(
                        {
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                        }
                    )
                else:
                    amount_currency = -(
                        operation.product_uom_qty * operation.price_unit
                    )
                    balance = currency._convert(
                        amount_currency,
                        company.currency_id,
                        company,
                        fields.Date.today(),
                    )
                    invoice_line_vals.update(
                        {
                            "amount_currency": amount_currency,
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                            "currency_id": currency.id,
                        }
                    )
                invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))

            # Create invoice lines from fees.
            for fee in repair.fees_lines:
                invoice_line_vals = fee._prepare_invoice_line()
                if group:
                    invoice_line_vals["name"] = repair.name + "-" + fee.name

                if currency == company.currency_id:
                    balance = -(fee.product_uom_qty * fee.price_unit)
                    invoice_line_vals.update(
                        {
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                        }
                    )
                else:
                    amount_currency = -(fee.product_uom_qty * fee.price_unit)
                    balance = currency._convert(
                        amount_currency,
                        company.currency_id,
                        company,
                        fields.Date.today(),
                    )
                    invoice_line_vals.update(
                        {
                            "amount_currency": amount_currency,
                            "debit": balance > 0.0 and balance or 0.0,
                            "credit": balance < 0.0 and -balance or 0.0,
                            "currency_id": currency.id,
                        }
                    )
                invoice_vals["invoice_line_ids"].append((0, 0, invoice_line_vals))

        # Create invoices.
        invoices_vals_list_per_company = defaultdict(list)
        for (
            _partner_invoice_id,
            _currency_id,
            company_id,
        ), invoices in grouped_invoices_vals.items():
            for invoice in invoices:
                invoices_vals_list_per_company[company_id].append(invoice)

        for company_id, invoices_vals_list in invoices_vals_list_per_company.items():
            # VFE TODO remove the default_company_id ctxt key ?
            # Account fallbacks on self.env.company, which is correct with with_company
            self.env["account.move"].with_company(company_id).with_context(
                default_company_id=company_id, default_move_type="out_invoice"
            ).create(invoices_vals_list)

        repairs.write({"invoiced": True})
        repairs.mapped("operations").filtered(lambda op: op.type == "add").write(
            {"invoiced": True}
        )
        repairs.mapped("fees_lines").write({"invoiced": True})

        for repair in repairs:
            repair._split_invoice(group=False)

        return {repair.id: repair.invoice_id.id for repair in repairs}

    def _split_invoice(self, group=False):
        self.ensure_one()

        document_type_list = []

        inv_ids = []
        invoice_created_by_super = self.invoice_id
        inv_ids += invoice_created_by_super
        for inv_line in invoice_created_by_super.invoice_line_ids:
            if inv_line.display_type or not inv_line.fiscal_operation_line_id:
                continue

            fiscal_document_type = inv_line.fiscal_operation_line_id.get_document_type(
                inv_line.move_id.company_id
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
                        if group
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
                        # inv_ids = inv_ids + invoice
                    elif group_key in invoices:
                        if order.name not in invoices_origin[group_key]:
                            invoices_origin[group_key].append(order.name)
                        if (
                            order.client_order_ref
                            and order.client_order_ref not in invoices_name[group_key]
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
                        # order_line = self.order_line.filtered(
                        #     lambda x: x.invoice_lines in inv_line
                        # )
                        # if len(order_line.invoice_lines) > 1:
                        #     # TODO: É valido tratar isso no caso de já ter mais
                        #     #  faturas geradas e vinvuladas a linha
                        #     continue
                        # else:
                        #     order_line.invoice_lines = invoice.invoice_line_ids
                        invoice_created_by_super.invoice_line_ids -= inv_line

        invoice_created_by_super.document_serie_id = (
            fiscal_document_type.get_document_serie(
                invoice_created_by_super.company_id,
                invoice_created_by_super.fiscal_operation_id,
            )
        )
