# Copyright (C) 2022 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class SaleCommissionMakeInvoice(models.TransientModel):
    _inherit = "sale.commission.make.invoice"

    def _default_commission_document_type_id(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        document_type_id = get_param(
            "l10n_br_sale_commission.commission_document_type_id"
        )
        document_type_search = False
        if document_type_id:
            # TODO - Diferenças entre usar o search e o browse
            #  l10n_br_fiscal.document.type(39,)
            #  l10n_br_fiscal.document.type('39',)
            #  No caso do browse com aspas '39' retorna erro na tela ao abrir
            #  o wizard:
            #      Database fetch misses ids (('39',)) and has extra ids ((39,)),
            #      may be caused by a type incoherence in a previous request/
            #  Testar na migração
            # document_type = (
            #     self.env["l10n_br_fiscal.document.type"]
            #     .sudo()
            #    .browse(document_type_id)

            document_type_search = (
                self.env["l10n_br_fiscal.document.type"]
                .sudo()
                .search([("id", "=", document_type_id)])
            )
        return document_type_search

    def _default_fiscal_operation_id(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        fiscal_operation_id = get_param(
            "l10n_br_sale_commission.commission_fiscal_operation_id"
        )
        fiscal_operation = False
        if fiscal_operation_id:
            # TODO - Mesmo erro da diferença entre o objeto com aspas
            fiscal_operation = self.env["l10n_br_fiscal.operation"].search(
                [("id", "=", fiscal_operation_id)]
            )

        return fiscal_operation

    def _default_product(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        product_id = get_param("l10n_br_sale_commission.commission_product_id")
        product = False
        if product_id:
            # TODO - Mesmo erro da diferença entre o objeto com aspas
            product = self.env["product.product"].search([("id", "=", product_id)])

        return product

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
    product = fields.Many2one(
        default=_default_product,
    )

    def button_create(self):
        self.ensure_one()
        return super(
            SaleCommissionMakeInvoice,
            self.with_context(
                document_type_id=self.commission_document_type_id.id,
                fiscal_operation_id=self.fiscal_operation_id.id,
            ),
        ).button_create()

    @api.onchange("commission_document_type_id")
    def _onchange_commission_document_type_id(self):
        for record in self:
            if record.commission_document_type_id:
                return {"domain": {"product": [("fiscal_type", "=", "09")]}}
            else:
                record.fiscal_operation_id = False
                return {"domain": {"product": False}}
