# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

from ..constants.fiscal import (
    FISCAL_IN_OUT, TAX_FRAMEWORK,
   TAX_BASE_TYPE, TAX_BASE_TYPE_PERCENT,
   TAX_DOMAIN_ICMS, TAX_DOMAIN_IPI, TAX_DOMAIN_PIS,
   TAX_DOMAIN_PIS_ST, TAX_DOMAIN_COFINS, TAX_DOMAIN_COFINS_ST
)


class DocumentFiscalLineMixin(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.mixin"
    _description = "Document Fiscal Mixin"

    @api.model
    def _default_operation(self):
        return False

    @api.model
    def _operation_domain(self):
        domain = [('state', '=', 'approved')]
        return domain

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.ref('base.BRL'))

    operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        domain=lambda self: self._operation_domain(),
        default=_default_operation)

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related="operation_id.operation_type",
        string="Operation Type",
        readonly=True)

    operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        domain="[('operation_id', '=', operation_id), "
               "('state', '=', 'approved')]")

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        domain="[('type_in_out', '=', operation_type)]")

    fiscal_quantity = fields.Float(
        string="Fiscal Quantity",
        digits=dp.get_precision("Product Unit of Measure"))

    fiscal_price = fields.Float(
        string="Fiscal Price",
        digits=dp.get_precision("Product Price"))

    fiscal_tax_ids = fields.Many2many(
        comodel_name='l10n_br_fiscal.tax',
        relation='fiscal_tax_rel',
        column1='document_id',
        column2='fiscal_tax_id',
        string="Fiscal Taxes")

    # ICMS Fields
    icms_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS",
        domain="[('tax_domain', '=', 'icms')]",
    )

    icms_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST ICMS",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'icms')]",
    )

    icms_base = fields.Monetary(string="ICMS Base")

    icms_percent = fields.Float(string="ICMS %")

    icms_reduction = fields.Float(string="ICMS % Reduction")

    icms_value = fields.Monetary(string="ICMS Value")

    # ICMS Simples Nacional Fields
    icmssn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS SN",
        domain="[('tax_domain', '=', 'icmssn')]",
    )

    icmssn_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CSOSN",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'icmssn')]",
    )

    icmssn_credit_value = fields.Monetary(string="ICMS SN Credit")

    # IPI Fields
    ipi_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IPI",
        domain="[('tax_domain', '=', 'ipi')]",
    )

    ipi_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IPI",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'ipi')]",
    )

    ipi_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="IPI Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    ipi_base = fields.Monetary(string="IPI Base")

    ipi_percent = fields.Float(string="IPI %")

    ipi_reduction = fields.Float(string="IPI % Reduction")

    ipi_value = fields.Monetary(string="IPI Value")

    ipi_guideline_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline",
        string="IPI Guideline",
        domain="['|', ('cst_in_id', '=', ipi_cst_id),"
        "('cst_out_id', '=', ipi_cst_id)]",
    )

    # PIS/COFINS Fields
    # COFINS
    cofins_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS",
        domain="[('tax_domain', '=', 'cofins')]",
    )

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'cofins')]",
    )

    cofins_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    cofins_base = fields.Monetary(string="COFINS Base")

    cofins_percent = fields.Float(string="COFINS %")

    cofins_reduction = fields.Float(string="COFINS % Reduction")

    cofins_value = fields.Monetary(string="COFINS Value")

    cofins_base_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.base", string="COFINS Base"
    )

    cofins_credit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.credit",
        string="COFINS Credit")

    # COFINS ST
    cofinsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS ST",
        domain="[('tax_domain', '=', 'cofinsst')]")

    cofinsst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS ST",
        domain="[('cst_type', '=', operation_type),"
               "('tax_domain', '=', 'cofinsst')]",
    )

    cofinsst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    cofinsst_base = fields.Monetary(string="COFINS ST Base")

    cofinsst_percent = fields.Float(string="COFINS ST %")

    cofinsst_reduction = fields.Float(string="COFINS ST % Reduction")

    cofinsst_value = fields.Monetary(string="COFINS ST Value")

    # PIS
    pis_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS",
        domain="[('tax_domain', '=', 'pis')]",
    )

    pis_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'pis')]",
    )

    pis_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    pis_base = fields.Monetary(string="PIS Base")

    pis_percent = fields.Float(string="PIS %")

    pis_reduction = fields.Float(string="PIS % Reduction")

    pis_value = fields.Monetary(string="PIS Value")

    pis_base_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.base", string="PIS Base Code"
    )

    pis_credit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.credit", string="PIS Credit"
    )

    # PIS ST
    pisst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS ST",
        domain="[('tax_domain', '=', 'pisst')]",
    )

    pisst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS ST",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'pisst')]",
    )

    pisst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS ST Base Type",
        default=TAX_BASE_TYPE_PERCENT,
        required=True,
    )

    pisst_base = fields.Monetary(string="PIS ST Base")

    pisst_percent = fields.Float(string="PIS ST %")

    pisst_reduction = fields.Float(string="PIS ST % Reduction")

    pisst_value = fields.Monetary(string="PIS ST Value")

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False):

        model_view = super(DocumentFiscalLineMixin, self).fields_view_get(
            view_id, view_type, toolbar, submenu)

        return model_view # TO REMOVE

        if view_type == "form":
            fiscal_view = self.env.ref("l10n_br_fiscal.document_fiscal_line_mixin_form")

            doc = etree.fromstring(model_view.get("arch"))

            for fiscal_node in doc.xpath("//group[@name='l10n_br_fiscal']"):
                sub_view_node = etree.fromstring(fiscal_view["arch"])

                try:
                    fiscal_node.getparent().replace(fiscal_node, sub_view_node)
                    model_view["arch"] = etree.tostring(doc, encoding="unicode")
                except ValueError:
                    return model_view

        return model_view

    @api.multi
    def _update_fiscal_taxes(self):
        for d in self:
            d.fiscal_tax_ids = d.operation_line_id.get_fiscal_taxes(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id)

            for tax in d.fiscal_tax_ids:
                if tax.tax_domain == TAX_DOMAIN_IPI:
                    d.ipi_tax_id = tax
                if tax.tax_domain == TAX_DOMAIN_PIS:
                    d.pis_tax_id = tax
                if tax.tax_domain == TAX_DOMAIN_COFINS:
                    d.cofins_tax_id = tax

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
                self._update_fiscal_taxes()

                if self.partner_id.state_id == self.company_id.state_id:
                    self.cfop_id = self.operation_line_id.cfop_internal_id
                elif self.partner_id.state_id != self.company_id.state_id:
                    self.cfop_id = self.operation_line_id.cfop_external_id
                elif self.partner_id.country_id != self.company_id.country_id:
                    self.cfop_id = self.operation_line_id.cfop_export_id

    def _set_fields_icms(self, tax_dict):
        if tax_dict:
            self.icms_cst_id = self.icms_tax_id.cst_from_tax(self.operation_type)
            self.icms_base_type = tax_dict.get("base_type")
            self.icms_base = tax_dict.get("base")
            self.icms_percent = tax_dict.get("percent_amount")
            self.icms_reduction = tax_dict.get("percent_reduction")
            self.icms_value = tax_dict.get("tax_value")

    @api.onchange("icms_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_icms_tax_id(self):
        if self.icms_tax_id:
            result_taxes = self._compute_taxes(self.icms_tax_id)
            self._set_fields_icms(result_taxes.get(TAX_DOMAIN_ICMS))
        else:
            self.icms_cst_id = False

    @api.onchange("icms_base", "icms_percent", "icms_reduction", "icms_value")
    def _onchange_icms_fields(self):
        pass

    @api.onchange("icmssn_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_icmssn_tax_id(self):
        if self.icmssn_tax_id:
            self.icmssn_cst_id = self.icmssn_tax_id.cst_from_tax(self.operation_type)

    @api.onchange("icms_base", "icms_percent", "icms_reduction", "icms_value")
    def _onchange_icmssn_fields(self):
        pass

    def _set_fields_ipi(self, tax_dict):
        if tax_dict:
            self.ipi_cst_id = self.ipi_tax_id.cst_from_tax(self.operation_type)
            self.ipi_base_type = tax_dict.get("base_type")
            self.ipi_base = tax_dict.get("base")
            self.ipi_percent = tax_dict.get("percent_amount")
            self.ipi_reduction = tax_dict.get("percent_reduction")
            self.ipi_value = tax_dict.get("tax_value")

    @api.onchange("ipi_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_ipi_tax_id(self):
        if self.ipi_tax_id:
            result_taxes = self._compute_taxes(self.ipi_tax_id)
            self._set_fields_ipi(result_taxes.get(TAX_DOMAIN_IPI))
        else:
            self.ipi_cst_id = False

    @api.onchange("ipi_base", "ipi_percent", "ipi_reduction", "ipi_value")
    def _onchange_ipi_fields(self):
        pass

    def _set_fields_pis(self, tax_dict):
        if tax_dict:
            self.pis_cst_id = self.pis_tax_id.cst_from_tax(self.operation_type)
            self.pis_base_type = tax_dict.get("base_type")
            self.pis_base = tax_dict.get("base")
            self.pis_percent = tax_dict.get("percent_amount")
            self.pis_reduction = tax_dict.get("percent_reduction")
            self.pis_value = tax_dict.get("tax_value")

    @api.onchange("pis_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_pis_tax_id(self):
        if self.pis_tax_id:
            result_taxes = self._compute_taxes(self.pis_tax_id)
            self._set_fields_pis(result_taxes.get(TAX_DOMAIN_PIS))
        else:
            self.pis_cst_id = False

    @api.onchange(
        "pis_base_type", "pis_base", "pis_percent", "pis_reduction", "pis_value"
    )
    def _onchange_pis_fields(self):
        pass

    def _set_fields_pisst(self, tax_dict):
        if tax_dict:
            self.pisst_cst_id = self.pisst_tax_id.cst_from_tax(
                self.operation_type)
            self.pisst_base_type = tax_dict.get("base_type")
            self.pisst_base = tax_dict.get("base")
            self.pisst_percent = tax_dict.get("percent_amount")
            self.pisst_reduction = tax_dict.get("percent_reduction")
            self.pisst_value = tax_dict.get("tax_value")

    @api.onchange("pisst_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_pisst_tax_id(self):
        if self.pisst_tax_id:
            result_taxes = self._compute_taxes(self.pisst_tax_id)
            self._set_fields_pisst(result_taxes.get(TAX_DOMAIN_PIS_ST))
        else:
            self.pisst_cst_id = False

    @api.onchange("pisst_base")
    def _onchange_pisst_fields(self):
        pass

    def _set_fields_cofins(self, tax_dict):
        if tax_dict:
            self.cofins_cst_id = self.cofins_tax_id.cst_from_tax(self.operation_type)
            self.cofins_base_type = tax_dict.get("base_type")
            self.cofins_base = tax_dict.get("base")
            self.cofins_percent = tax_dict.get("percent_amount")
            self.cofins_reduction = tax_dict.get("percent_reduction")
            self.cofins_value = tax_dict.get("tax_value")

    @api.onchange("cofins_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_cofins_tax_id(self):
        if self.cofins_tax_id:
            result_taxes = self._compute_taxes(self.cofins_tax_id)
            self._set_fields_cofins(result_taxes.get(TAX_DOMAIN_COFINS))
        else:
            self.cofins_cst_id = False

    @api.onchange(
        "cofins_base_type",
        "cofins_base",
        "cofins_percent",
        "cofins_reduction",
        "cofins_value",
    )
    def _onchange_cofins_fields(self):
        pass

    def _set_fields_cofinsst(self, tax_dict):
        if tax_dict:
            self.cofinsst_cst_id = self.cofinsst_tax_id.cst_from_tax(
                self.operation_type)
            self.cofinsst_base_type = tax_dict.get("base_type")
            self.cofinsst_base = tax_dict.get("base")
            self.cofinsst_percent = tax_dict.get("percent_amount")
            self.cofinsst_reduction = tax_dict.get("percent_reduction")
            self.cofinsst_value = tax_dict.get("tax_value")

    @api.onchange("cofinsst_tax_id", "fiscal_price", "fiscal_quantity")
    def _onchange_cofinsst_tax_id(self):
        if self.cofinsst_tax_id:
            result_taxes = self._compute_taxes(self.cofinsst_tax_id)
            self._set_fields_cofinsst(result_taxes.get(TAX_DOMAIN_COFINS_ST))
        else:
            self.cofinsst_cst_id = False

    @api.onchange("cofinsst_base", "fiscal_price", "fiscal_quantity")
    def _onchange_cofins_fields(self):
        pass
