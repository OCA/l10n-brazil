# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    commission_gen_br_fiscal_doc = fields.Boolean(
        string="Generate Brazilian Fiscal Document",
        config_parameter="l10n_sale_commission.commission_gen_br_fiscal_doc",
        help="When create the invoice for commission payment should"
        " generate Brazilian Fiscal Document.",
    )

    commission_document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Default Fiscal Document",
        domain="[('type', '=', 'service')]",
        config_parameter="l10n_br_sale_commission.commission_document_type_id",
        # config_parameter=""
        help="Default Brazilian Fiscal Document for Fiscal"
        " Document at Commission payment.",
    )

    commission_fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Default Fiscal Operation",
        config_parameter="l10n_br_sale_commission.commission_fiscal_operation_id",
        help="Default Brazilian Fiscal Operation for"
        " Fiscal Document at Commission payment.",
    )

    commission_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Default Product for invoicing",
        config_parameter="l10n_br_sale_commission.commission_product_id",
        help="Default Commission Product for invoicing.",
    )

    @api.onchange("commission_gen_br_fiscal_doc")
    def _onchange_commission_gen_br_fiscal_doc(self):
        if not self.commission_gen_br_fiscal_doc:
            self.commission_document_type_id = False
            self.commission_fiscal_operation_id = False

    @api.onchange("commission_document_type_id")
    def _onchange_commission_document_type_id(self):
        for record in self:
            if record.commission_document_type_id:
                return {
                    "domain": {"commission_product_id": [("fiscal_type", "=", "09")]}
                }
            else:
                record.commission_fiscal_operation_id = False
                return {"domain": {"commission_product_id": False}}
