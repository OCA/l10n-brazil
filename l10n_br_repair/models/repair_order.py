# Copyright 2020 - TODAY, Marcel Savegnago - Escodoo - https://www.escodoo.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import is_html_empty


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
        return [("state", "=", "approved")]

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
        string="Copy Repair quotation notes in Fiscal documents",
        default=_default_copy_note,
    )

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related="partner_id.cnpj_cpf",
    )

    legal_name = fields.Char(
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="State Tax Number/RG",
        related="partner_id.inscr_est",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="repair_order_comment_rel",
        column1="repair_id",
        column2="comment_id",
        string="Comments",
    )

    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="Invoices",
        compute="_compute_invoice_ids",
    )

    invoice_count = fields.Integer(
        compute="_compute_invoice_ids",
    )

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "operations"

    def _get_amount_lines(self):
        """Repair parts to add and fees are the lines of the fiscal document."""
        lines = []
        for repair in self:
            lines += list(repair.operations.filtered(lambda op: op.type == "add"))
            lines += list(repair.fees_lines)
        return lines

    def _get_product_amount_lines(self):
        """Lines that receive the freight, insurance and other costs informed
        by total (it must be a recordset, see _distribute_amount_to_lines)."""
        return self.operations.filtered(
            lambda op: op.type == "add" and op.product_id.type != "service"
        )

    def _get_fiscal_amount_field_dependencies(self):
        if self._abstract:
            return []
        dependencies = ["operations.type"]
        amount_fields = self._get_amount_fields()
        for o2m_field_name in ("operations", "fees_lines"):
            line_fields = self[o2m_field_name]._fields
            dependencies.append(o2m_field_name)
            for field in amount_fields:
                line_field = field.replace("amount_", "")
                if line_field in line_fields:
                    dependencies.append(f"{o2m_field_name}.{line_field}")
        return dependencies

    @api.depends(
        "operations.price_unit",
        "operations.product_uom_qty",
        "operations.product_id",
        "operations.price_total",
        "operations.price_subtotal",
        "fees_lines.price_unit",
        "fees_lines.product_uom_qty",
        "fees_lines.product_id",
        "fees_lines.price_total",
        "fees_lines.price_subtotal",
        "pricelist_id.currency_id",
        "partner_id",
        "fiscal_operation_id",
    )
    def _amount_tax(self):
        br_orders = self.filtered("fiscal_operation_id")
        for order in br_orders:
            lines = order._get_amount_lines()
            amount = sum(line.price_total - line.price_subtotal for line in lines)
            order.amount_tax = order.pricelist_id.currency_id.round(amount)
        return super(RepairOrder, self - br_orders)._amount_tax()

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form" and self.env.company.country_id.code == "BR":
            arch = self.env["repair.line"].inject_fiscal_fields(arch)
        return arch, view

    @api.depends(
        "invoice_id",
        "operations.invoice_line_id",
        "fees_lines.invoice_line_id",
    )
    def _compute_invoice_ids(self):
        for order in self:
            invoices = (
                order.invoice_id
                | order.operations.invoice_line_id.move_id
                | order.fees_lines.invoice_line_id.move_id
            )
            invoices |= invoices.reversal_move_id
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    def action_created_invoice(self):
        self.ensure_one()
        if self.invoice_count <= 1:
            return super().action_created_invoice()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = [("id", "in", self.invoice_ids.ids)]
        action["context"] = {"create": False}
        return action

    def action_repair_cancel(self):
        draft_invoices = self.mapped("invoice_ids").filtered(
            lambda move: move.state == "draft"
        )
        if draft_invoices:
            draft_invoices.button_cancel()
        return super().action_repair_cancel()

    def _get_invoice_document_type(self, line):
        self.ensure_one()
        if not line.fiscal_operation_line_id:
            raise UserError(
                _(
                    "The repair line %(line)s of %(repair)s has no fiscal "
                    "operation line, so it is not possible to know which fiscal "
                    "document must be issued.",
                    line=line.name,
                    repair=self.name,
                )
            )
        return line.fiscal_operation_line_id.get_document_type(self.company_id)

    def _prepare_br_invoice(self, partner_invoice, fiscal_position, document_type):
        self.ensure_one()
        currency = self.pricelist_id.currency_id
        narration = self.quotation_notes
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": partner_invoice.id,
            "partner_shipping_id": self.address_id.id,
            "currency_id": currency.id,
            "narration": narration if not is_html_empty(narration) else "",
            "invoice_origin": self.name,
            "repair_ids": [Command.link(self.id)],
            "invoice_line_ids": [],
            "fiscal_position_id": fiscal_position.id,
            "company_id": self.company_id.id,
        }
        if partner_invoice.property_payment_term_id:
            invoice_vals[
                "invoice_payment_term_id"
            ] = partner_invoice.property_payment_term_id.id

        fiscal_values = self._prepare_br_fiscal_dict()
        # The invoicing address chosen by the user has priority
        fiscal_values["partner_id"] = partner_invoice.id
        invoice_vals.update(fiscal_values)

        invoice_vals["document_type_id"] = document_type.id
        document_serie = document_type.get_document_serie(
            self.company_id, self.fiscal_operation_id
        )
        if document_serie:
            invoice_vals["document_serie_id"] = document_serie.id
        if self.fiscal_operation_id.journal_id:
            invoice_vals["journal_id"] = self.fiscal_operation_id.journal_id.id
        return invoice_vals

    def _create_invoices(self, group=False):
        """Create one invoice for each fiscal document type (for instance
        NF-e for the parts and NFS-e for the fees) when the repair order has
        a fiscal operation. Repair orders without fiscal operation keep the
        standard behavior."""
        br_repairs = self.filtered("fiscal_operation_id")
        result = {}
        if self - br_repairs:
            result = super(RepairOrder, self - br_repairs)._create_invoices(group=group)

        repairs = br_repairs.filtered(
            lambda repair: repair.state not in ("draft", "cancel")
            and not repair.invoice_id
            and repair.invoice_method != "none"
        )
        grouped_invoices_vals = {}
        for repair in repairs:
            repair = repair.with_company(repair.company_id)
            partner_invoice = repair.partner_invoice_id or repair.partner_id
            if not partner_invoice:
                raise UserError(
                    _("You have to select an invoice address in the repair form.")
                )
            fiscal_position = self.env["account.fiscal.position"]._get_fiscal_position(
                partner_invoice, delivery=repair.address_id
            )
            currency = repair.pricelist_id.currency_id

            for line in repair._get_amount_lines():
                if not line.product_id:
                    raise UserError(_("No product defined on fees."))
                document_type = repair._get_invoice_document_type(line)
                if group:
                    key = (
                        partner_invoice.id,
                        currency.id,
                        repair.company_id.id,
                        document_type.id,
                    )
                    name = f"{repair.name}-{line.name}"
                else:
                    key = (repair.id, document_type.id)
                    name = line.name

                invoice_vals = grouped_invoices_vals.get(key)
                if invoice_vals is None:
                    invoice_vals = repair._prepare_br_invoice(
                        partner_invoice, fiscal_position, document_type
                    )
                    grouped_invoices_vals[key] = invoice_vals
                elif repair.name not in invoice_vals["invoice_origin"].split(", "):
                    invoice_vals["invoice_origin"] += ", " + repair.name
                    invoice_vals["repair_ids"].append(Command.link(repair.id))

                invoice_vals["invoice_line_ids"].append(
                    Command.create(line._prepare_br_invoice_line(fiscal_position, name))
                )

        invoices_vals_per_company = defaultdict(list)
        for invoice_vals in grouped_invoices_vals.values():
            invoices_vals_per_company[invoice_vals["company_id"]].append(invoice_vals)
        for company_id, invoices_vals_list in invoices_vals_per_company.items():
            self.env["account.move"].with_company(company_id).with_context(
                default_company_id=company_id, default_move_type="out_invoice"
            ).create(invoices_vals_list)

        repairs.write({"invoiced": True})
        repairs.mapped("operations").filtered(lambda op: op.type == "add").write(
            {"invoiced": True}
        )
        repairs.mapped("fees_lines").write({"invoiced": True})

        result.update({repair.id: repair.invoice_id.id for repair in repairs})
        return result
