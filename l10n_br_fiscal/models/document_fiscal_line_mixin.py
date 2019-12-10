# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
from odoo import api, fields, models

from ..constants.fiscal import FISCAL_IN_OUT, TAX_FRAMEWORK


class DocumentFiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.mixin"
    _description = "Document Fiscal Mixin"

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related="operation_id.operation_type",
        string="Operation Type",
        readonly=True,
    )

    operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        domain="[('state', '=', 'approved')]",
        string="Operation",
    )

    operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('operation_id', '=', operation_id), " "('state', '=', 'approved')]",
    )

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        domain="[('type_in_out', '=', operation_type)]",
    )

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        model_view = super(DocumentFiscalLineMixin, self).fields_view_get(
            view_id, view_type, toolbar, submenu
        )

        if view_type == "form":
            import pudb; pudb.set_trace()
            fiscal_view = self.env.ref("l10n_br_fiscal.document_fiscal_line_mixin_form")

            doc = etree.fromstring(model_view.get("arch"))

            for fiscal_node in doc.xpath("//group[@id='l10n_br_fiscal']"):
                sub_view_node = etree.fromstring(fiscal_view["arch"])

                try:
                    fiscal_node.getparent().replace(fiscal_node, sub_view_node)
                    model_view["arch"] = etree.tostring(doc, encoding="unicode")
                except ValueError:
                    return model_view

        return model_view

    @api.multi
    def compute_taxes(self):
        pass

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        if self.operation_id:
            price = {
                "sale_price": self.product_id.list_price,
                "cost_price": self.product_id.standard_price,
            }

            self.price = price.get(self.operation_id.default_price_unit, 0.00)

            self.operation_line_id = self.operation_id.line_definition(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id,
            )

            if self.operation_line_id:
                if self.partner_id.state_id == self.company_id.state_id:
                    self.cfop_id = self.operation_line_id.cfop_internal_id
                elif self.partner_id.state_id != self.company_id.state_id:
                    self.cfop_id = self.operation_line_id.cfop_external_id
                elif self.partner_id.country_id != self.company_id.country_id:
                    self.cfop_id = self.operation_line_id.cfop_export_id

            # Get and define default and operation taxes
            self.compute_taxes()
