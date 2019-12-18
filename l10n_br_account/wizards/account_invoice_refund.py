# Copyright (C) 2013  Florian da Costa - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
from odoo import _, api, fields, models
from odoo.osv.orm import setup_modifiers
from ..models.account_invoice import REFUND_TO_OPERATION, FISCAL_TYPE_REFUND
from odoo.exceptions import Warning as UserError


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    force_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Force Fiscal Operation",
    )

    @api.multi
    def compute_refund(self, mode="refund"):
        inv_obj = self.env["account.invoice"]
        context = dict(self.env.context)

        for send_invoice in inv_obj.browse(context.get("active_ids")):
            result = super(AccountInvoiceRefund, self).compute_refund(mode)
            domain = result["domain"]

            ids_domain = [x for x in domain if x[0] == "id"][0]
            invoice_ids = ids_domain[2]
            for invoice in inv_obj.browse(invoice_ids):

                if not invoice.document_type_id:
                    continue

                if (
                    not self.force_fiscal_operation_id
                    and not invoice.operation_id
                ):
                    raise UserError(_("Document without Operation !"))

                if (
                    not self.force_fiscal_operation_id
                    and not invoice.operation_id.return_operation_id
                ):
                    raise UserError(
                        _(
                            "Fiscal Operation: There is not Return Operation "
                            "for %s !"
                        )
                        % invoice.operation_id.name
                    )

                invoice.operation_id = (
                    self.force_fiscal_operation_id.id
                    or invoice.operation_id.return_operation_id.id
                )

                invoice_values = {
                    "operation_id": invoice.operation_id.id,
                }

                for line in invoice.invoice_line_ids:
                    if (
                        not self.force_fiscal_operation_id
                        and not line.operation_id
                    ):
                        raise UserError(_("Document line without Operation !"))

                    if (
                        not self.force_fiscal_operation_id
                        and not line.operation_id.refund_operation_id
                    ):
                        raise UserError(
                            _(
                                "Fiscal Operation: There is not Return "
                                "Operation for %s !"
                            )
                            % line.operation_id.name
                        )

                    line.operation_id = (
                        self.force_fiscal_operation_id.id
                        or line.operation_id.return_operation_id
                    )

                    line._onchange_operation_id()

                    line_values = {
                        "operation_id": line.operation_id.id,
                        "operation_line_id": line.operation_line_id.id,
                    }
                    line.write(line_values)
                invoice.write(invoice_values)
            return result

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        result = super(AccountInvoiceRefund, self).fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        invoice_type = self.env.context.get("type", "out_invoice")
        operation_type = REFUND_TO_OPERATION[invoice_type]
        fiscal_type = FISCAL_TYPE_REFUND[operation_type]
        eview = etree.fromstring(result["arch"])
        operation_id = eview.xpath("//field[@name='force_fiscal_operation_id']")
        for field in operation_id:
            field.set(
                "domain",
                "[('operation_type', '=', '%s'), ('fiscal_type', 'in', %s)]"
                % (operation_type, fiscal_type),
            )
            setup_modifiers(field)
        result["arch"] = etree.tostring(eview)
        return result
