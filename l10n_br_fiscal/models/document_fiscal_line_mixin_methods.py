# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from copy import deepcopy

from lxml import etree

from odoo import api, models

from ..constants.icms import ICMS_BASE_TYPE_DEFAULT, ICMS_ST_BASE_TYPE_DEFAULT
from .tax import TAX_DICT_VALUES

FISCAL_TAX_ID_FIELDS = [
    "cofins_tax_id",
    "cofins_wh_tax_id",
    "cofinsst_tax_id",
    "csll_tax_id",
    "csll_wh_tax_id",
    "icms_tax_id",
    "icmsfcp_tax_id",
    "icmssn_tax_id",
    "icmsst_tax_id",
    "ii_tax_id",
    "inss_tax_id",
    "inss_wh_tax_id",
    "ipi_tax_id",
    "irpj_tax_id",
    "irpj_wh_tax_id",
    "issqn_tax_id",
    "issqn_wh_tax_id",
    "pis_tax_id",
    "pis_wh_tax_id",
    "pisst_tax_id",
]

FISCAL_CST_ID_FIELDS = [
    "icms_cst_id",
    "ipi_cst_id",
    "pis_cst_id",
    "pisst_cst_id",
    "cofins_cst_id",
    "cofinsst_cst_id",
]


class FiscalDocumentLineMixinMethods(models.AbstractModel):
    _name = "l10n_br_fiscal.document.line.mixin.methods"
    _description = "Document Fiscal Mixin Methods"

    @api.model
    def inject_fiscal_fields(
        self,
        view_arch,
        view_ref="l10n_br_fiscal.document_fiscal_line_mixin_form",
        xpath_mappings=None,
    ):
        """
        Injects common fiscal fields into view placeholder elements.
        Used for invoice line, sale order line, purchase order line...
        """
        fiscal_view = self.env.ref(
            "l10n_br_fiscal.document_fiscal_line_mixin_form"
        ).sudo()
        fsc_doc = etree.fromstring(fiscal_view["arch"])
        doc = etree.fromstring(view_arch)

        if xpath_mappings is None:
            xpath_mappings = (
                # (placeholder_xpath, fiscal_xpath)
                (".//group[@name='fiscal_fields']", "//group[@name='fiscal_fields']"),
                (".//page[@name='fiscal_taxes']", "//page[@name='fiscal_taxes']"),
                (
                    ".//page[@name='fiscal_line_extra_info']",
                    "//page[@name='fiscal_line_extra_info']",
                ),
                # these will only collect (invisible) fields for onchanges:
                (
                    ".//control[@name='fiscal_taxes_fields']...",
                    "//page[@name='fiscal_taxes']//field",
                ),
                (
                    ".//control[@name='fiscal_line_extra_info_fields']...",
                    "//page[@name='fiscal_line_extra_info']//field",
                ),
            )
        for placeholder_xpath, fiscal_xpath in xpath_mappings:
            fiscal_nodes = fsc_doc.xpath(fiscal_xpath)
            for target_node in doc.findall(placeholder_xpath):
                if len(fiscal_nodes) == 1:
                    # replace unique placeholder
                    # (deepcopy is required to inject fiscal nodes in possible
                    # next places)
                    replace_node = deepcopy(fiscal_nodes[0])
                    target_node.getparent().replace(target_node, replace_node)
                else:
                    # append multiple fields to placeholder container
                    for fiscal_node in fiscal_nodes:
                        field = deepcopy(fiscal_node)
                        if not field.attrib.get("optional"):
                            field.attrib["invisible"] = "1"
                        target_node.append(field)
        return doc

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        model_view = super().fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == "form":
            arch_tree = self.inject_fiscal_fields(model_view["arch"])
            View = self.env["ir.ui.view"]
            # Override context for postprocessing
            if view_id and model_view.get("base_model", self._name) != self._name:
                View = View.with_context(base_model_name=model_view["base_model"])

            # Apply post processing, groups and modifiers etc...
            xarch, xfields = View.postprocess_and_fields(
                node=arch_tree, model=self._name
            )
            model_view["arch"] = xarch
            model_view["fields"] = xfields
        return model_view

    @api.depends(
        "fiscal_price",
        "discount_value",
        "insurance_value",
        "other_value",
        "freight_value",
        "fiscal_quantity",
        "amount_tax_not_included",
        "uot_id",
        "product_id",
        "partner_id",
        "company_id",
    )
    def _compute_amounts(self):
        for record in self:
            round_curr = record.currency_id or self.env.ref("base.BRL")
            # Valor dos produtos
            record.price_gross = round_curr.round(record.price_unit * record.quantity)

            record.amount_untaxed = record.price_gross - record.discount_value

            record.amount_fiscal = (
                round_curr.round(record.fiscal_price * record.fiscal_quantity)
                - record.discount_value
            )

            record.amount_tax = record.amount_tax_not_included

            add_to_amount = sum([record[a] for a in record._add_fields_to_amount()])
            rm_to_amount = sum([record[r] for r in record._rm_fields_to_amount()])

            # Valor do documento (NF)
            record.amount_total = (
                record.amount_untaxed + record.amount_tax + add_to_amount - rm_to_amount
            )

            # Valor Liquido (TOTAL + IMPOSTOS - RETENÇÕES)
            record.amount_taxed = record.amount_total - record.amount_tax_withholding

            # Valor financeiro
            if (
                record.fiscal_operation_line_id
                and record.fiscal_operation_line_id.add_to_amount
                and (not record.cfop_id or record.cfop_id.finance_move)
            ):
                record.financial_total = record.amount_taxed
                record.financial_total_gross = (
                    record.financial_total + record.discount_value
                )
                record.financial_discount_value = record.discount_value
            else:
                record.financial_total_gross = record.financial_total = 0.0
                record.financial_discount_value = 0.0

    def _compute_taxes(self, taxes, cst=None):
        self.ensure_one()
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
            other_value=self.other_value,
            freight_value=self.freight_value,
            ncm=self.ncm_id,
            nbs=self.nbs_id,
            nbm=self.nbm_id,
            cest=self.cest_id,
            operation_line=self.fiscal_operation_line_id,
            icmssn_range=self.icmssn_range_id,
            icms_origin=self.icms_origin,
            icms_cst_id=self.icms_cst_id,
            ind_final=self.ind_final,
        )

    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.line.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop("id", None)

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    def _get_all_tax_id_fields(self):
        self.ensure_one()
        taxes = self.env["l10n_br_fiscal.tax"]

        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            taxes |= self[fiscal_tax_field]

        return taxes

    def _remove_all_fiscal_tax_ids(self):
        for line in self:
            line.fiscal_tax_ids = False

            for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
                line[fiscal_tax_field] = False

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

    def _update_fiscal_tax_ids(self, taxes):
        for line in self:
            taxes_groups = line.fiscal_tax_ids.mapped("tax_domain")
            fiscal_taxes = line.fiscal_tax_ids.filtered(
                lambda ft: ft.tax_domain not in taxes_groups
            )
            line.fiscal_tax_ids = fiscal_taxes + taxes

    def _update_taxes(self):
        for line in self:
            compute_result = self._compute_taxes(line.fiscal_tax_ids)
            computed_taxes = compute_result.get("taxes", {})
            line.amount_tax_included = compute_result.get("amount_included", 0.0)
            line.amount_tax_not_included = compute_result.get(
                "amount_not_included", 0.0
            )
            line.amount_tax_withholding = compute_result.get("amount_withholding", 0.0)
            line.estimate_tax = compute_result.get("estimate_tax", 0.0)
            for tax in line.fiscal_tax_ids:
                computed_tax = computed_taxes.get(tax.tax_domain, {})
                if hasattr(line, "%s_tax_id" % (tax.tax_domain,)):
                    # since v13, when line is a new record,
                    # line.fiscal_tax_ids recordset is made of
                    # NewId records with an origin pointing back to the original
                    # tax. tax.ids[0] is a way to the the single original tax back.
                    setattr(line, "%s_tax_id" % (tax.tax_domain,), tax.ids[0])
                    method = getattr(self, "_set_fields_%s" % (tax.tax_domain,))
                    if method:
                        method(computed_tax)

    def _get_product_price(self):
        self.ensure_one()
        price = {
            "sale_price": self.product_id.list_price,
            "cost_price": self.product_id.standard_price,
        }

        self.price_unit = price.get(self.fiscal_operation_id.default_price_unit, 0.00)

    def __document_comment_vals(self):
        self.ensure_one()
        return {
            "user": self.env.user,
            "ctx": self._context,
            "doc": self.document_id,
            "item": self,
        }

    def _document_comment(self):
        for d in self:
            d.additional_data = d.comment_ids.compute_message(
                d.__document_comment_vals(), d.manual_additional_data
            )

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            if not self.price_unit:
                self._get_product_price()
            self._onchange_commercial_quantity()
            self.fiscal_operation_line_id = self.fiscal_operation_id.line_definition(
                company=self.company_id,
                partner=self.partner_id,
                product=self.product_id,
            )
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
                cest=self.cest_id,
                city_taxation_code=self.city_taxation_code_id,
                ind_final=self.ind_final,
            )

            self.cfop_id = mapping_result["cfop"]
            self.ipi_guideline_id = mapping_result["ipi_guideline"]
            taxes = self.env["l10n_br_fiscal.tax"]
            for tax in mapping_result["taxes"].values():
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
                    lambda r: r.city_id == company_city_id
                )
                if city_id:
                    self.city_taxation_code_id = city_id
                    self.issqn_fg_city_id = company_city_id
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
        self.ensure_one()
        if tax_dict:
            self.issqn_base = tax_dict.get("base")
            self.issqn_percent = tax_dict.get("percent_amount")
            self.issqn_reduction = tax_dict.get("percent_reduction")
            self.issqn_value = tax_dict.get("tax_value")

    @api.onchange("issqn_base", "issqn_percent", "issqn_reduction", "issqn_value")
    def _onchange_issqn_fields(self):
        pass

    def _set_fields_issqn_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.issqn_wh_base = tax_dict.get("base")
            self.issqn_wh_percent = tax_dict.get("percent_amount")
            self.issqn_wh_reduction = tax_dict.get("percent_reduction")
            self.issqn_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "issqn_wh_base", "issqn_wh_percent", "issqn_wh_reduction", "issqn_wh_value"
    )
    def _onchange_issqn_wh_fields(self):
        pass

    def _set_fields_csll(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.csll_base = tax_dict.get("base")
            self.csll_percent = tax_dict.get("percent_amount")
            self.csll_reduction = tax_dict.get("percent_reduction")
            self.csll_value = tax_dict.get("tax_value")

    @api.onchange("csll_base", "csll_percent", "csll_reduction", "csll_value")
    def _onchange_csll_fields(self):
        pass

    def _set_fields_csll_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.csll_wh_base = tax_dict.get("base")
            self.csll_wh_percent = tax_dict.get("percent_amount")
            self.csll_wh_reduction = tax_dict.get("percent_reduction")
            self.csll_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "csll_wh_base", "csll_wh_percent", "csll_wh_reduction", "csll_wh_value"
    )
    def _onchange_csll_wh_fields(self):
        pass

    def _set_fields_irpj(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.irpj_base = tax_dict.get("base")
            self.irpj_percent = tax_dict.get("percent_amount")
            self.irpj_reduction = tax_dict.get("percent_reduction")
            self.irpj_value = tax_dict.get("tax_value")

    @api.onchange("irpj_base", "irpj_percent", "irpj_reduction", "irpj_value")
    def _onchange_irpj_fields(self):
        pass

    def _set_fields_irpj_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.irpj_wh_base = tax_dict.get("base")
            self.irpj_wh_percent = tax_dict.get("percent_amount")
            self.irpj_wh_reduction = tax_dict.get("percent_reduction")
            self.irpj_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "irpj_wh_base", "irpj_wh_percent", "irpj_wh_reduction", "irpj_wh_value"
    )
    def _onchange_irpj_wh_fields(self):
        pass

    def _set_fields_inss(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.inss_base = tax_dict.get("base")
            self.inss_percent = tax_dict.get("percent_amount")
            self.inss_reduction = tax_dict.get("percent_reduction")
            self.inss_value = tax_dict.get("tax_value")

    @api.onchange("inss_base", "inss_percent", "inss_reduction", "inss_value")
    def _onchange_inss_fields(self):
        pass

    def _set_fields_inss_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.inss_wh_base = tax_dict.get("base")
            self.inss_wh_percent = tax_dict.get("percent_amount")
            self.inss_wh_reduction = tax_dict.get("percent_reduction")
            self.inss_wh_value = tax_dict.get("tax_value")

    @api.onchange(
        "inss_wh_base", "inss_wh_percent", "inss_wh_reduction", "inss_wh_value"
    )
    def _onchange_inss_wh_fields(self):
        pass

    def _set_fields_icms(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.icms_cst_id = tax_dict.get("cst_id")
            self.icms_base_type = tax_dict.get("icms_base_type", ICMS_BASE_TYPE_DEFAULT)
            self.icms_base = tax_dict.get("base")
            self.icms_percent = tax_dict.get("percent_amount")
            self.icms_reduction = tax_dict.get("percent_reduction")
            self.icms_value = tax_dict.get("tax_value")

            # vBCUFDest - Valor da BC do ICMS na UF de destino
            if tax_dict.get("icms_dest_base") is not None:
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
            if tax_dict.get("icms_origin_value") is not None:
                self.icms_origin_value = tax_dict.get("icms_origin_value")

            # vICMSUFDest - Valor do ICMS Interestadual para a UF de destino
            if tax_dict.get("icms_dest_value") is not None:
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
        "icms_origin_value",
    )
    def _onchange_icms_fields(self):
        pass

    def _set_fields_icmssn(self, tax_dict):
        self.ensure_one()
        self.icms_cst_id = tax_dict.get("cst_id")
        self.icmssn_base = tax_dict.get("base")
        self.icmssn_percent = tax_dict.get("percent_amount")
        self.icmssn_reduction = tax_dict.get("percent_reduction")
        self.icmssn_credit_value = tax_dict.get("tax_value")
        self.simple_value = self.icmssn_base * self.icmssn_range_id.total_tax_percent
        self.simple_without_icms_value = self.simple_value - self.icmssn_credit_value

    @api.onchange(
        "icmssn_base", "icmssn_percent", "icmssn_reduction", "icmssn_credit_value"
    )
    def _onchange_icmssn_fields(self):
        pass

    def _set_fields_icmsst(self, tax_dict):
        self.ensure_one()
        self.icmsst_base_type = tax_dict.get(
            "icmsst_base_type", ICMS_ST_BASE_TYPE_DEFAULT
        )
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
        "icmsst_wh_value",
    )
    def _onchange_icmsst_fields(self):
        pass

    def _set_fields_icmsfcp(self, tax_dict):
        self.ensure_one()
        self.icmsfcp_base = tax_dict.get("base", 0.0)
        self.icmsfcp_percent = tax_dict.get("percent_amount", 0.0)
        self.icmsfcp_value = tax_dict.get("tax_value", 0.0)
        self.icmsfcpst_value = tax_dict.get("fcpst_value", 0.0)

    @api.onchange("icmsfcp_percent", "icmsfcp_value")
    def _onchange_icmsfcp_fields(self):
        pass

    def _set_fields_ipi(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.ipi_cst_id = tax_dict.get("cst_id")
            self.ipi_base_type = tax_dict.get("base_type", False)
            self.ipi_base = tax_dict.get("base", 0.00)
            self.ipi_percent = tax_dict.get("percent_amount", 0.00)
            self.ipi_reduction = tax_dict.get("percent_reduction", 0.00)
            self.ipi_value = tax_dict.get("tax_value", 0.00)

    @api.onchange("ipi_base", "ipi_percent", "ipi_reduction", "ipi_value")
    def _onchange_ipi_fields(self):
        pass

    def _set_fields_ii(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.ii_base = tax_dict.get("base", 0.00)
            self.ii_percent = tax_dict.get("percent_amount", 0.00)
            self.ii_value = tax_dict.get("tax_value", 0.00)

    @api.onchange("ii_base", "ii_percent", "ii_value")
    def _onchange_ii_fields(self):
        pass

    def _set_fields_pis(self, tax_dict):
        self.ensure_one()
        if tax_dict:
            self.pis_cst_id = tax_dict.get("cst_id")
            self.pis_base_type = tax_dict.get("base_type")
            self.pis_base = tax_dict.get("base", 0.00)
            self.pis_percent = tax_dict.get("percent_amount", 0.00)
            self.pis_reduction = tax_dict.get("percent_reduction", 0.00)
            self.pis_value = tax_dict.get("tax_value", 0.00)

    @api.onchange(
        "pis_base_type", "pis_base", "pis_percent", "pis_reduction", "pis_value"
    )
    def _onchange_pis_fields(self):
        pass

    def _set_fields_pis_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
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
        "pis_wh_value",
    )
    def _onchange_pis_wh_fields(self):
        pass

    def _set_fields_pisst(self, tax_dict):
        self.ensure_one()
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
        "pisst_value",
    )
    def _onchange_pisst_fields(self):
        pass

    def _set_fields_cofins(self, tax_dict):
        self.ensure_one()
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
        "cofins_value",
    )
    def _onchange_cofins_fields(self):
        pass

    def _set_fields_cofins_wh(self, tax_dict):
        self.ensure_one()
        if tax_dict:
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
        "cofins_wh_value",
    )
    def _onchange_cofins_wh_fields(self):
        pass

    def _set_fields_cofinsst(self, tax_dict):
        self.ensure_one()
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
        "cofinsst_value",
    )
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
        "other_value",
        "freight_value",
    )
    def _onchange_fiscal_taxes(self):
        self._update_fiscal_tax_ids(self._get_all_tax_id_fields())
        self._update_taxes()

    @api.model
    def _update_fiscal_quantity(self, product_id, price, quantity, uom_id, uot_id):
        result = {"uot_id": uom_id, "fiscal_quantity": quantity, "fiscal_price": price}
        if uot_id and uom_id != uot_id:
            result["uot_id"] = uot_id
            if product_id and price and quantity:
                product = self.env["product.product"].browse(product_id)
                result["fiscal_price"] = price / (product.uot_factor or 1.0)
                result["fiscal_quantity"] = quantity * (product.uot_factor or 1.0)

        return result

    @api.onchange("uot_id", "uom_id", "price_unit", "quantity")
    def _onchange_commercial_quantity(self):
        product_id = False
        if self.product_id:
            product_id = self.product_id.id
        self.update(
            self._update_fiscal_quantity(
                product_id, self.price_unit, self.quantity, self.uom_id, self.uot_id
            )
        )

    @api.onchange("ncm_id", "nbs_id", "cest_id")
    def _onchange_ncm_id(self):
        self._onchange_fiscal_operation_id()

    @api.onchange("fiscal_tax_ids")
    def _onchange_fiscal_tax_ids(self):
        self._update_taxes()

    @api.onchange("city_taxation_code_id")
    def _onchange_city_taxation_code_id(self):
        if self.city_taxation_code_id:
            self.cnae_id = self.city_taxation_code_id.cnae_id
            self._onchange_fiscal_operation_id()

    @api.model
    def _add_fields_to_amount(self):
        return ["insurance_value", "other_value", "freight_value"]

    @api.model
    def _rm_fields_to_amount(self):
        return ["icms_relief_value"]
