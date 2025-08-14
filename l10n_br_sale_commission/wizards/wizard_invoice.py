# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Renato Lima <renato.lima@akretion.com.br>
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class CommissionMakeInvoice(models.TransientModel):
    _inherit = "commission.make.invoice"

    def _default_commission_document_type_id(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        document_type_id = get_param(
            "l10n_br_sale_commission.commission_document_type_id"
        )
        if document_type_id:
            return (
                self.env["l10n_br_fiscal.document.type"]
                .sudo()
                .browse(int(document_type_id))
            )

    def _default_fiscal_operation_id(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        fiscal_operation_id = get_param(
            "l10n_br_sale_commission.commission_fiscal_operation_id"
        )
        if fiscal_operation_id:
            return self.env["l10n_br_fiscal.operation"].browse(int(fiscal_operation_id))

    def _default_product_id(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        product_id = get_param("l10n_br_sale_commission.commission_product_id")
        if product_id:
            return self.env["product.product"].browse(int(product_id))

    commission_gen_br_fiscal_doc = fields.Boolean(
        string="Generate Brazilian Fiscal Document",
        default=lambda s: s.env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_sale_commission.commission_gen_br_fiscal_doc"),
    )

    commission_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Fiscal Document",
        domain="[('type', '=', 'service')]",
        default=_default_commission_document_type_id,
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        default=_default_fiscal_operation_id,
    )

    product_id = fields.Many2one(
        default=_default_product_id, domain="[('id', 'in', allowed_product_ids)]"
    )

    allowed_product_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_allowed_product_ids",
    )

    def button_create(self):
        self.ensure_one()
        return super(
            CommissionMakeInvoice,
            self.with_context(
                document_type_id=self.commission_document_type_id.id,
                fiscal_operation_id=self.fiscal_operation_id.id,
            ),
        ).button_create()

    @api.depends("commission_document_type_id")
    def _compute_allowed_product_ids(self):
        for record in self:
            fiscal_type_domain = []
            if self.commission_document_type_id:
                fiscal_type_domain = [("fiscal_type", "=", "09")]

            record.allowed_product_ids = self.env["product.product"].search(
                fiscal_type_domain
            )
