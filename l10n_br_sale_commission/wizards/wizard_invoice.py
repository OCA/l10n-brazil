# Copyright (C) 2022 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class SaleCommissionMakeInvoice(models.TransientModel):
    _inherit = "sale.commission.make.invoice"

    def _default_document_type_id(self):
        return self.env.ref("l10n_br_fiscal.document_SE", raise_if_not_found=False)

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Fiscal Document",
        domain="[('type', '=', 'service')]",
        default=_default_document_type_id,
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
    )

    def button_create(self):
        self.ensure_one()
        return super(
            SaleCommissionMakeInvoice,
            self.with_context(
                document_type_id=self.document_type_id.id,
                fiscal_operation_id=self.fiscal_operation_id.id,
            ),
        ).button_create()
