# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import api, models
from odoo.osv.orm import setup_modifiers

from .tax import TAX_DICT_VALUES

from ..constants.fiscal import (
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_WH,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_CSLL,
    TAX_DOMAIN_CSLL_WH,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_ICMS_SN,
    TAX_DOMAIN_ICMS_ST,
    TAX_DOMAIN_II,
    TAX_DOMAIN_INSS,
    TAX_DOMAIN_INSS_WH,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_IRPJ,
    TAX_DOMAIN_IRPJ_WH,
    TAX_DOMAIN_ISSQN,
    TAX_DOMAIN_ISSQN_WH,
    TAX_DOMAIN_PIS,
    TAX_DOMAIN_PIS_WH,
    TAX_DOMAIN_PIS_ST,
)

from ..constants.icms import (
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ST_BASE_TYPE_DEFAULT
)

FISCAL_TAX_ID_FIELDS = [
    'cofins_tax_id',
    'cofins_wh_tax_id',
    'cofinsst_tax_id',
    'csll_tax_id',
    'csll_wh_tax_id',
    'icms_tax_id',
    'icmsfcp_tax_id',
    'icmssn_tax_id',
    'icmsst_tax_id',
    'ii_tax_id',
    'inss_tax_id',
    'inss_wh_tax_id',
    'ipi_tax_id',
    'irpj_tax_id',
    'irpj_wh_tax_id',
    'issqn_tax_id',
    'issqn_wh_tax_id',
    'pis_tax_id',
    'pis_wh_tax_id',
    'pisst_tax_id',
]

FISCAL_CST_ID_FIELDS = [
    'icms_cst_id',
    'ipi_cst_id',
    'pis_cst_id',
    'pisst_cst_id',
    'cofins_cst_id',
    'cofinsst_cst_id'
]


class FiscalDocumentLineMixinMethods(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.line.mixin.methods'
    _description = 'Document Fiscal Mixin Methods'

    @api.model
    def fiscal_form_view(self, form_view_arch):
        try:

            fiscal_view = self.env.ref(
                "l10n_br_fiscal.document_fiscal_line_mixin_form")

            view_template_tags = {
                'group': ['fiscal_fields'],
                'page': ['fiscal_taxes', 'fiscal_line_extra_info'],
            }

            fsc_doc = etree.fromstring(fiscal_view["arch"])
            doc = etree.fromstring(form_view_arch)

            for tag, tag_names in view_template_tags.items():
                for tag_name in tag_names:
                    fiscal_node = fsc_doc.xpath(
                        "//{0}[@name='{1}']".format(tag, tag_name))[0]

                    doc_node = doc.xpath(
                        "//{0}[@name='{1}']".format(tag, tag_name))[0]

                    setup_modifiers(doc_node)
                    for n in doc_node.getiterator():
                        setup_modifiers(n)

                    doc_node.getparent().replace(doc_node, fiscal_node)

            form_view_arch = etree.tostring(doc, encoding='unicode')
        except Exception:
            return form_view_arch

        return form_view_arch

    @api.model
    def fields_view_get(self, view_id=None, view_type="form",
                        toolbar=False, submenu=False):
        model_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu)

        if view_type == 'form':
            model_view["arch"] = self.fiscal_form_view(model_view["arch"])

        View = self.env['ir.ui.view']
        # Override context for postprocessing
        if view_id and model_view.get('base_model', self._name) != self._name:
            View = View.with_context(base_model_name=model_view['base_model'])

        # Apply post processing, groups and modifiers etc...
        xarch, xfields = View.postprocess_and_fields(
            self._name, etree.fromstring(model_view['arch']), view_id)
        model_view['arch'] = xarch
        model_view['fields'] = xfields
        return model_view

    def _compute_taxes(self, taxes, cst=None):
        return taxes.compute_taxes(
            company=self.company_id,
            partner=self.partner_id,
            product=self.product_id,
            price_unit=self.price_unit,
            quantity=self.quantity,
            uom_id=self.uom_id,
            fiscal_price=self.fiscal_price,
            fiscal_quantity=self.fiscal_quantity,
            uot_id=self.uot_id,
            discount_value=self.discount_value,
            insurance_value=self.insurance_value,
            other_costs_value=self.other_costs_value,
            freight_value=self.freight_value,
            ncm=self.ncm_id,
            nbs=self.nbs_id,
            nbm=self.nbm_id,
            cest=self.cest_id,
            operation_line=self.fiscal_operation_line_id,
            icmssn_range=self.icmssn_range_id,
            icms_origin=self.icms_origin)

    @api.multi
    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.line.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop('id', None)

        # this will force to create a new fiscal document line:
        vals['fiscal_document_line_id'] = False

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.multi
    def _get_all_tax_id_fields(self):
        self.ensure_one()
        taxes = self.env['l10n_br_fiscal.tax']

        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            taxes |= self[fiscal_tax_field]

        return taxes

    @api.multi
    def _remove_all_fiscal_tax_ids(self):
        for l in self:
            l.fiscal_tax_ids = False

            for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
                l[fiscal_tax_field] = False

            self._set_fields_issqn(TAX_DICT_VALUES)
            self._set_fields_csll(TAX_DICT_VALUES)
            self._set_fields_irpj(TAX_DICT_VALUES)
            self._set_fields_inss(TAX_DICT_VALUES)
            self._set_fields_icms(TAX_DICT_VALUES)
            self._set_fields_icmsfcp(TAX_DICT_VALUES)
            self._set_fields_icmsst(TAX_DICT_VALUES)
            self._set_fields_icmssn(TAX_DICT_VALUES)
            self._set_fields_ipi(TAX_DICT_VALUES)
            self._set_fields_ii(TAX_DICT_VALUES)
            self._set_fields_pis(TAX_DICT_VALUES)
            self._set_fields_pisst(TAX_DICT_VALUES)
            self._set_fields_cofins(TAX_DICT_VALUES)
            self._set_fields_cofinsst(TAX_DICT_VALUES)
            self._set_fields_issqn_wh(TAX_DICT_VALUES)
            self._set_fields_pis_wh(TAX_DICT_VALUES)
            self._set_fields_cofins_wh(TAX_DICT_VALUES)
            self._set_fields_csll_wh(TAX_DICT_VALUES)
            self._set_fields_irpj_wh(TAX_DICT_VALUES)
            self._set_fields_inss_wh(TAX_DICT_VALUES)

    @api.multi
    def _update_fiscal_tax_ids(self, taxes):
        for l in self:
            taxes_groups = l.fiscal_tax_ids.mapped('tax_domain')
            fiscal_taxes = l.fiscal_tax_ids.filtered(
                lambda ft: ft.tax_domain not in taxes_groups)

            l.fiscal_tax_ids = fiscal_taxes + taxes

    @api.multi
    def _update_taxes(self):
        for l in self:
            compute_result = self._compute_taxes(l.fiscal_tax_ids)
            computed_taxes = compute_result.get('taxes', {})
            l.amount_tax_not_included = compute_result.get(
                'amount_not_included', 0.0)
            l.amount_tax_withholding = compute_result.get(
                'amount_withholding', 0.0)
            l.amount_estimate_tax = compute_result.get(
                'amount_estimate_tax', 0.0)
            for tax in l.fiscal_tax_ids:

                computed_tax = computed_taxes.get(tax.tax_domain, {})

                if tax.tax_domain == TAX_DOMAIN_IPI:
                    l.ipi_tax_id = tax
                    self._set_fields_ipi(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_II:
                    l.ii_tax_id = tax
                    self._set_fields_ii(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_PIS:
                    l.pis_tax_id = tax
                    self._set_fields_pis(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_PIS_ST:
                    l.pisst_tax_id = tax
                    self._set_fields_pisst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_COFINS:
                    l.cofins_tax_id = tax
                    self._set_fields_cofins(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_COFINS_ST:
                    l.cofinsst_tax_id = tax
                    self._set_fields_cofinsst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS:
                    l.icms_tax_id = tax
                    self._set_fields_icms(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_SN:
                    l.icmssn_tax_id = tax
                    self._set_fields_icmssn(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_ST:
                    l.icmsst_tax_id = tax
                    self._set_fields_icmsst(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ICMS_FCP:
                    l.icmsfcp_tax_id = tax
                    self._set_fields_icmsfcp(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_ISSQN:
                    l.issqn_tax_id = tax
                    self._set_fields_issqn(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_CSLL:
                    l.csll_tax_id = tax
                    self._set_fields_csll(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_IRPJ:
                    l.irpj_tax_id = tax
                    self._set_fields_irpj(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_INSS:
                    l.inss_tax_id = tax
                    self._set_fields_inss(computed_tax)

                if tax.tax_domain == TAX_DOMAIN_ISSQN_WH:
                    l.issqn_wh_tax_id = tax
                    self._set_fields_issqn_wh(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_PIS_WH:
                    l.pis_wh_tax_id = tax
                    self._set_fields_pis_wh(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_COFINS_WH:
                    l.cofins_wh_tax_id = tax
                    self._set_fields_cofins_wh(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_CSLL_WH:
                    l.csll_wh_tax_id = tax
                    self._set_fields_csll_wh(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_IRPJ_WH:
                    l.irpj_wh_tax_id = tax
                    self._set_fields_irpj_wh(computed_tax)
                if tax.tax_domain == TAX_DOMAIN_INSS_WH:
                    l.inss_wh_tax_id = tax
                    self._set_fields_inss_wh(computed_tax)

    def _get_product_price(self):
        price = {
            'sale_price': self.product_id.list_price,
            'cost_price': self.product_id.standard_price,
        }

        self.price_unit = price.get(
            self.fiscal_operation_id.default_price_unit, 0.00)

    def _document_comment_vals(self):
        return {
            'user': self.env.user,
            'ctx': self._context,
            'doc': self.document_id,
            'item': self,
        }

    def document_comment(self):
        for d in self.filtered('comment_ids'):
            d.additional_data = d.additional_data or ''
            d.additional_data += d.comment_ids.compute_message(
                d._document_comment_vals())

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            if not self.price_unit:
                self._get_product_price()

            self._onchange_commercial_quantity()

            self.fiscal_operation_line_id = self.fiscal_operation_id.line_definition(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id)

            self._onchange_fiscal_operation_line_id()

    @api.onchange("fiscal_operation_line_id")
    def _onchange_fiscal_operation_line_id(self):

        # Reset Taxes
        self._remove_all_fiscal_tax_ids()
        if self.fiscal_operation_line_id:

            mapping_result = self.fiscal_operation_line_id.map_fiscal_taxes(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id,
                ncm=self.ncm_id,
                nbm=self.nbm_id,
                nbs=self.nbs_id,
                cest=self.cest_id)

            self.cfop_id = mapping_result['cfop']
            taxes = self.env['l10n_br_fiscal.tax']
            for tax in mapping_result['taxes'].values():
                taxes |= tax
            self.fiscal_tax_ids = taxes
            self._update_taxes()
            self.comment_ids = self.fiscal_operation_line_id.comment_ids

        if not self.fiscal_operation_line_id:
            self.cfop_id = False

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.fiscal_type = self.product_id.fiscal_type
            self.uom_id = self.product_id.uom_id
            self.ncm_id = self.product_id.ncm_id
            self.nbm_id = self.product_id.nbm_id
            self.tax_icms_or_issqn = self.product_id.tax_icms_or_issqn
            self.icms_origin = self.product_id.icms_origin
            self.cest_id = self.product_id.cest_id
            self.nbs_id = self.product_id.nbs_id
            self.fiscal_genre_id = self.product_id.fiscal_genre_id
            self.service_type_id = self.product_id.service_type_id
            self.uot_id = self.product_id.uot_id or self.product_id.uom_id
            if self.product_id.city_taxation_code_id:
                company_city_id = self.company_id.city_id
                city_id = self.product_id.city_taxation_code_id.filtered(
                    lambda r: r.city_id == company_city_id)
                if city_id:
                    self.city_taxation_code_id = city_id
        else:
            self.name = False
            self.fiscal_type = False
            self.uom_id = False
            self.ncm_id = False
            self.nbm_id = False
            self.tax_icms_or_issqn = False
            self.icms_origin = False
            self.cest_id = False
            self.nbs_id = False
            self.fiscal_genre_id = False
            self.service_type_id = False
            self.city_taxation_code_id = False
            self.uot_id = False

        self._get_product_price()
        self._onchange_fiscal_operation_id()

    def _set_fields_issqn(self, tax_dict):
        if tax_dict:
            self.issqn_base = tax_dict.get("base")
            self.issqn_percent = tax_dict.get("percent_amount")
            self.issqn_reduction = tax_dict.get("percent_reduction")
            self.issqn_value = tax_dict.get("tax_value")

    @api.onchange(
        "issqn_base",
        "issqn_percent",
        "issqn_reduction",
        "issqn_value")
    def _onchange_issqn_fields(self):
        pass

    def _set_fields_issqn_wh(self, tax_dict):
        if tax_dict:
            self.issqn_wh_base = tax_dict.get("base")
            self.issqn_wh_percent = tax_dict.get("percent_amount")
            self.issqn_wh_reduction = tax_dict.get("percent_reduction")
            self.issqn_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "issqn_wh_base",
        "issqn_wh_percent",
        "issqn_wh_reduction",
        "issqn_wh_value")
    def _onchange_issqn_wh_fields(self):
        pass

    def _set_fields_csll(self, tax_dict):
        if tax_dict:
            self.csll_base = tax_dict.get("base")
            self.csll_percent = tax_dict.get("percent_amount")
            self.csll_reduction = tax_dict.get("percent_reduction")
            self.csll_value = tax_dict.get("tax_value")

    @api.onchange(
        "csll_base",
        "csll_percent",
        "csll_reduction",
        "csll_value")
    def _onchange_csll_fields(self):
        pass

    def _set_fields_csll_wh(self, tax_dict):
        if tax_dict:
            self.csll_wh_base = tax_dict.get("base")
            self.csll_wh_percent = tax_dict.get("percent_amount")
            self.csll_wh_reduction = tax_dict.get("percent_reduction")
            self.csll_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "csll_wh_base",
        "csll_wh_percent",
        "csll_wh_reduction",
        "csll_wh_value")
    def _onchange_csll_wh_fields(self):
        pass

    def _set_fields_irpj(self, tax_dict):
        if tax_dict:
            self.irpj_base = tax_dict.get("base")
            self.irpj_percent = tax_dict.get("percent_amount")
            self.irpj_reduction = tax_dict.get("percent_reduction")
            self.irpj_value = tax_dict.get("tax_value")

    @api.onchange(
        "irpj_base",
        "irpj_percent",
        "irpj_reduction",
        "irpj_value")
    def _onchange_irpj_fields(self):
        pass

    def _set_fields_irpj_wh(self, tax_dict):
        if tax_dict:
            self.irpj_wh_base = tax_dict.get("base")
            self.irpj_wh_percent = tax_dict.get("percent_amount")
            self.irpj_wh_reduction = tax_dict.get("percent_reduction")
            self.irpj_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "irpj_wh_base",
        "irpj_wh_percent",
        "irpj_wh_reduction",
        "irpj_wh_value")
    def _onchange_irpj_wh_fields(self):
        pass

    def _set_fields_inss(self, tax_dict):
        if tax_dict:
            self.inss_base = tax_dict.get("base")
            self.inss_percent = tax_dict.get("percent_amount")
            self.inss_reduction = tax_dict.get("percent_reduction")
            self.inss_value = tax_dict.get("tax_value")

    @api.onchange(
        "inss_base",
        "inss_percent",
        "inss_reduction",
        "inss_value")
    def _onchange_inss_fields(self):
        pass

    def _set_fields_inss_wh(self, tax_dict):
        if tax_dict:
            self.inss_wh_base = tax_dict.get("base")
            self.inss_wh_percent = tax_dict.get("percent_amount")
            self.inss_wh_reduction = tax_dict.get("percent_reduction")
            self.inss_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "inss_wh_base",
        "inss_wh_percent",
        "inss_wh_reduction",
        "inss_wh_value")
    def _onchange_inss_wh_fields(self):
        pass

    def _set_fields_icms(self, tax_dict):
        if tax_dict:
            self.icms_cst_id = tax_dict.get("cst_id")
            self.icms_base_type = tax_dict.get(
                "icms_base_type", ICMS_BASE_TYPE_DEFAULT)
            self.icms_base = tax_dict.get("base")
            self.icms_percent = tax_dict.get("percent_amount")
            self.icms_reduction = tax_dict.get("percent_reduction")
            self.icms_value = tax_dict.get("tax_value")

            # vBCUFDest - Valor da BC do ICMS na UF de destino
            self.icms_destination_base = tax_dict.get("icms_dest_base")

            # pICMSUFDest - Alíquota interna da UF de destino
            self.icms_origin_percent = tax_dict.get("icms_origin_perc")

            # pICMSInter - Alíquota interestadual das UF envolvidas
            self.icms_destination_percent = tax_dict.get("icms_dest_perc")

            # pICMSInterPart - Percentual provisório de partilha
            # do ICMS Interestadual
            self.icms_sharing_percent = tax_dict.get("icms_sharing_percent")

            # vICMSUFRemet - Valor do ICMS Interestadual
            # para a UF do remetente
            self.icms_origin_value = tax_dict.get("icms_origin_value")

            # vICMSUFDest - Valor do ICMS Interestadual para a UF de destino
            self.icms_destination_value = tax_dict.get("icms_dest_value")

    @api.onchange(
        "icms_base",
        "icms_percent",
        "icms_reduction",
        "icms_value",
        "icms_destination_base",
        "icms_origin_percent",
        "icms_destination_percent",
        "icms_sharing_percent",
        "icms_origin_value")
    def _onchange_icms_fields(self):
        pass

    def _set_fields_icmssn(self, tax_dict):
        self.icms_cst_id = tax_dict.get("cst_id")
        self.icmssn_base = tax_dict.get("base")
        self.icmssn_percent = tax_dict.get("percent_amount")
        self.icmssn_reduction = tax_dict.get("percent_reduction")
        self.icmssn_credit_value = tax_dict.get("tax_value")
        self.simple_value = self.icmssn_base * self.icmssn_range_id.total_tax_percent
        self.simple_without_icms_value = self.simple_value - self.icmssn_credit_value

    @api.onchange(
        "icmssn_base",
        "icmssn_percent",
        "icmssn_reduction",
        "icmssn_credit_value")
    def _onchange_icmssn_fields(self):
        pass

    def _set_fields_icmsst(self, tax_dict):
        self.icmsst_base_type = tax_dict.get(
            "icmsst_base_type", ICMS_ST_BASE_TYPE_DEFAULT)
        self.icmsst_mva_percent = tax_dict.get("icmsst_mva_percent")
        self.icmsst_percent = tax_dict.get("percent_amount")
        self.icmsst_reduction = tax_dict.get("percent_reduction")
        self.icmsst_base = tax_dict.get("base")
        self.icmsst_value = tax_dict.get("tax_value")

        # TODO - OTHER TAX icmsst_wh_tax_id
        # self.icmsst_wh_base
        # self.icmsst_wh_value

    @api.onchange(
        "icmsst_base_type",
        "icmsst_mva_percent",
        "icmsst_percent",
        "icmsst_reduction",
        "icmsst_base",
        "icmsst_value",
        "icmsst_wh_base",
        "icmsst_wh_value")
    def _onchange_icmsst_fields(self):
        pass

    def _set_fields_icmsfcp(self, tax_dict):
        self.icmsfcp_base = tax_dict.get("base", 0.0)
        self.icmsfcp_percent = tax_dict.get("percent_amount", 0.0)
        self.icmsfcp_value = tax_dict.get("tax_value", 0.0)

    @api.onchange(
        "icmsfcp_percent",
        "icmsfcp_value")
    def _onchange_icmsfcp_fields(self):
        pass

    def _set_fields_ipi(self, tax_dict):
        if tax_dict:
            self.ipi_cst_id = tax_dict.get("cst_id")
            self.ipi_base_type = tax_dict.get("base_type", False)
            self.ipi_base = tax_dict.get("base", 0.00)
            self.ipi_percent = tax_dict.get("percent_amount", 0.00)
            self.ipi_reduction = tax_dict.get("percent_reduction", 0.00)
            self.ipi_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "ipi_base",
        "ipi_percent",
        "ipi_reduction",
        "ipi_value")
    def _onchange_ipi_fields(self):
        pass

    def _set_fields_ii(self, tax_dict):
        if tax_dict:
            self.ii_base = tax_dict.get("base", 0.00)
            self.ii_percent = tax_dict.get("percent_amount", 0.00)
            self.ii_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "ii_base",
        "ii_percent",
        "ii_value")
    def _onchange_ii_fields(self):
        pass

    def _set_fields_pis(self, tax_dict):
        if tax_dict:
            self.pis_cst_id = tax_dict.get("cst_id")
            self.pis_base_type = tax_dict.get("base_type")
            self.pis_base = tax_dict.get("base", 0.00)
            self.pis_percent = tax_dict.get("percent_amount", 0.00)
            self.pis_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pis_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pis_base_type",
        "pis_base",
        "pis_percent",
        "pis_reduction",
        "pis_value")
    def _onchange_pis_fields(self):
        pass

    def _set_fields_pis_wh(self, tax_dict):
        if tax_dict:
            self.pis_wh_cst_id = tax_dict.get("cst_id")
            self.pis_wh_base_type = tax_dict.get("base_type")
            self.pis_wh_base = tax_dict.get("base", 0.00)
            self.pis_wh_percent = tax_dict.get("percent_amount", 0.00)
            self.pis_wh_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pis_wh_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pis_wh_base_type",
        "pis_wh_base",
        "pis_wh_percent",
        "pis_wh_reduction",
        "pis_wh_value")
    def _onchange_pis_wh_fields(self):
        pass

    def _set_fields_pisst(self, tax_dict):
        if tax_dict:
            self.pisst_cst_id = tax_dict.get("cst_id")
            self.pisst_base_type = tax_dict.get("base_type")
            self.pisst_base = tax_dict.get("base", 0.00)
            self.pisst_percent = tax_dict.get("percent_amount", 0.00)
            self.pisst_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pisst_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pisst_base_type",
        "pisst_base",
        "pisst_percent",
        "pisst_reduction",
        "pisst_value")
    def _onchange_pisst_fields(self):
        pass

    def _set_fields_cofins(self, tax_dict):
        if tax_dict:
            self.cofins_cst_id = tax_dict.get("cst_id")
            self.cofins_base_type = tax_dict.get("base_type")
            self.cofins_base = tax_dict.get("base", 0.00)
            self.cofins_percent = tax_dict.get("percent_amount", 0.00)
            self.cofins_reduction = tax_dict.get("percent_reduction", 0.00)
            self.cofins_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "cofins_base_type",
        "cofins_base",
        "cofins_percent",
        "cofins_reduction",
        "cofins_value")
    def _onchange_cofins_fields(self):
        pass

    def _set_fields_cofins_wh(self, tax_dict):
        if tax_dict:
            self.cofins_wh_cst_id = tax_dict.get("cst_id")
            self.cofins_wh_base_type = tax_dict.get("base_type")
            self.cofins_wh_base = tax_dict.get("base", 0.00)
            self.cofins_wh_percent = tax_dict.get("percent_amount", 0.00)
            self.cofins_wh_reduction = tax_dict.get("percent_reduction", 0.00)
            self.cofins_wh_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "cofins_wh_base_type",
        "cofins_wh_base",
        "cofins_wh_percent",
        "cofins_wh_reduction",
        "cofins_wh_value")
    def _onchange_cofins_wh_fields(self):
        pass

    def _set_fields_cofinsst(self, tax_dict):
        if tax_dict:
            self.cofinsst_cst_id = tax_dict.get("cst_id")
            self.cofinsst_base_type = tax_dict.get("base_type")
            self.cofinsst_base = tax_dict.get("base", 0.00)
            self.cofinsst_percent = tax_dict.get("percent_amount", 0.00)
            self.cofinsst_reduction = tax_dict.get("percent_reduction", 0.00)
            self.cofinsst_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "cofinsst_base_type",
        "cofinsst_base",
        "cofinsst_percent",
        "cofinsst_reduction",
        "cofinsst_value")
    def _onchange_cofinsst_fields(self):
        pass

    @api.onchange(
        "csll_tax_id",
        "csll_wh_tax_id",
        "irpj_tax_id",
        "irpj_wh_tax_id",
        "inss_tax_id",
        "inss_wh_tax_id",
        "issqn_tax_id",
        "issqn_wh_tax_id",
        "icms_tax_id",
        "icmssn_tax_id",
        "icmsst_tax_id",
        "icmsfcp_tax_id",
        "ipi_tax_id",
        "ii_tax_id",
        "pis_tax_id",
        "pis_wh_tax_id",
        "pisst_tax_id",
        "cofins_tax_id",
        "cofins_wh_tax_id",
        "cofinsst_tax_id",
        "fiscal_price",
        "fiscal_quantity",
        "discount_value",
        "insurance_value",
        "other_costs_value",
        "freight_value")
    def _onchange_fiscal_taxes(self):
        self._update_fiscal_tax_ids(self._get_all_tax_id_fields())
        self._update_taxes()

    @api.onchange("uot_id", "uom_id", "price_unit", "quantity")
    def _onchange_commercial_quantity(self):
        if not self.uot_id:
            self.uot_id = self.uom_id

        if self.uom_id == self.uot_id:
            self.fiscal_price = self.price_unit
            self.fiscal_quantity = self.quantity

        if self.uom_id != self.uot_id:
            self.fiscal_price = self.price_unit / self.product_id.uot_factor
            self.fiscal_quantity = self.quantity * self.product_id.uot_factor

    @api.onchange("ncm_id", "nbs_id", "cest_id")
    def _onchange_ncm_id(self):
        self._onchange_fiscal_operation_id()

    @api.onchange('fiscal_tax_ids')
    def _onchange_fiscal_tax_ids(self):
        self._update_taxes()

    @api.onchange("city_taxation_code_id")
    def _onchange_city_taxation_code_id(self):
        if self.city_taxation_code_id:
            self.cnae_id = self.city_taxation_code_id.cnae_id
