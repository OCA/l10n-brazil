# Copyright (C) 2013  Florian da Costa - Akretion
# Copyright (C) 2021  Luis Felipe Miléo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, fields, models
from odoo.osv.orm import setup_modifiers

from ..models.account_invoice import FISCAL_TYPE_REFUND, REFUND_TO_OPERATION


class AccountInvoiceRefund(models.TransientModel):
    _inherit = "account.invoice.refund"

    force_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation", string="Force Fiscal Operation"
    )

    def invoice_refund(self):
        return super(
            AccountInvoiceRefund,
            self.with_context(
                force_fiscal_operation_id=self.force_fiscal_operation_id.id
            ),
        ).invoice_refund()

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        result = super().fields_view_get(view_id, view_type, toolbar, submenu)
        invoice_type = self.env.context.get("type", "out_invoice")
        fiscal_operation_type = REFUND_TO_OPERATION[invoice_type]
        fiscal_type = FISCAL_TYPE_REFUND[fiscal_operation_type]
        eview = etree.fromstring(result["arch"])
        fiscal_operation_id = eview.xpath("//field[@name='force_fiscal_operation_id']")

        for field in fiscal_operation_id:
            field.set(
                "domain",
                "[('fiscal_operation_type', '=', '%s'), ('fiscal_type', 'in', %s)]"
                % (fiscal_operation_type, fiscal_type),
            )
            setup_modifiers(field)
        result["arch"] = etree.tostring(eview)
        return result
