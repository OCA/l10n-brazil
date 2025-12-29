# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from copy import deepcopy

from lxml import etree
from lxml.builder import E

from odoo import Command, api, fields, models

from ..constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    FINAL_CUSTOMER,
    FISCAL_COMMENT_LINE,
    FISCAL_IN,
    FISCAL_TAX_ID_FIELDS,
    PRODUCT_FISCAL_TYPE,
    TAX_BASE_TYPE,
    TAX_BASE_TYPE_PERCENT,
    TAX_DOMAIN_CBS,
    TAX_DOMAIN_COFINS,
    TAX_DOMAIN_COFINS_ST,
    TAX_DOMAIN_COFINS_WH,
    TAX_DOMAIN_CSLL,
    TAX_DOMAIN_CSLL_WH,
    TAX_DOMAIN_IBS,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
    TAX_DOMAIN_ICMS_FCP_ST,
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
    TAX_DOMAIN_PIS_ST,
    TAX_DOMAIN_PIS_WH,
    TAX_FRAMEWORK_SIMPLES_ALL,
    TAX_ICMS_OR_ISSQN,
)
from ..constants.icms import (
    ICMS_BASE_TYPE,
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ORIGIN,
    ICMS_ORIGIN_DEFAULT,
    ICMS_ST_BASE_TYPE,
    ICMS_ST_BASE_TYPE_DEFAULT,
)
from ..constants.issqn import (
    ISSQN_ELIGIBILITY,
    ISSQN_ELIGIBILITY_DEFAULT,
    ISSQN_INCENTIVE,
    ISSQN_INCENTIVE_DEFAULT,
)


class FiscalDocumentLineMixin(models.AbstractModel):
    """
    Provides the primary field structure for Brazilian fiscal document lines.

    It is inherited by sale.order.line, purchase.order.linne, account.move.line
    and even stock.move in separate modules.
    Indeed these business documents need to take care of some fiscal parameters
    before creating Fiscal Document Lines. And of course,
    Fiscal Document Lines themselves inherit from this mixin.

    This abstract model defines an extensive set of fields necessary for
    line-item fiscal calculations and reporting in Brazil. It includes:
    - Product and quantity information.
    - Detailed fiscal classifications (NCM, CFOP, CEST, etc.).
    - Fields for each specific Brazilian tax (ICMS, IPI, PIS, COFINS,
      ISSQN, etc.), covering their respective bases, rates, and
      calculated values.
    - Line-level totals and cost components.
    """

    _name = "l10n_br_fiscal.document.line.mixin"
    _description = "Document Fiscal Mixin"

    @api.model
    def _default_icmssn_range_id(self):
        company = self.env.company
        stax_range_id = self.env["l10n_br_fiscal.simplified.tax.range"]

        if self.env.context.get("default_company_id"):
            company = self.env["res.company"].browse(
                self.env.context.get("default_company_id")
            )

        if company.tax_framework in TAX_FRAMEWORK_SIMPLES_ALL:
            stax_range_id = company.simplified_tax_range_id

        return stax_range_id

    @api.model
    def _operation_domain(self):
        domain = [("state", "=", "approved")]
        return domain

    @api.model
    def inject_fiscal_fields(
        self,
        doc,
        view_ref="l10n_br_fiscal.document_fiscal_line_mixin_form",
        xpath_mappings=None,
    ):
        """
        Inject common fiscal fields into view placeholder elements.
        Used for invoice line, sale order line, purchase order line...
        """

        # the list of computed fields we will add to the view when missing
        missing_line_fields = set(
            [
                fname
                for fname, _field in filter(
                    lambda item: item[1].compute
                    in (
                        "_compute_tax_fields",
                        "_compute_fiscal_tax_ids",
                        "_compute_product_fiscal_fields",
                    ),
                    self.env["l10n_br_fiscal.document.line.mixin"]._fields.items(),
                )
            ]
        )

        fiscal_view = self.env.ref(
            "l10n_br_fiscal.document_fiscal_line_mixin_form"
        ).sudo()
        fsc_doc = etree.fromstring(
            fiscal_view.with_context(inherit_branding=True).get_combined_arch()
        )

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
                    ".//control[@name='fiscal_fields']...",
                    "//group[@name='fiscal_fields']//field",
                ),
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
            placeholder_nodes = doc.findall(placeholder_xpath)
            if not placeholder_nodes:
                continue
            fiscal_nodes = fsc_doc.xpath(fiscal_xpath)
            for target_node in placeholder_nodes:
                if len(fiscal_nodes) == 1:
                    # replace unique placeholder
                    # (deepcopy is required to inject fiscal nodes in possible
                    # next places)
                    replace_node = deepcopy(fiscal_nodes[0])
                    target_node.getparent().replace(target_node, replace_node)
                else:
                    # append multiple fields to placeholder container
                    existing_fields = [
                        e.attrib["name"] for e in target_node if e.tag == "field"
                    ]
                    for fiscal_node in fiscal_nodes:
                        if fiscal_node.attrib["name"] in missing_line_fields:
                            missing_line_fields.remove(fiscal_node.attrib["name"])
                        if fiscal_node.attrib["name"] in existing_fields:
                            continue
                        field = deepcopy(fiscal_node)
                        if not field.attrib.get("optional"):
                            field.attrib["optional"] = "hide"
                        target_node.append(field)
                    for fname in missing_line_fields:
                        if fname not in existing_fields:
                            target_node.append(
                                E.field(name=fname, string=fname, optional="hide")
                            )
        return doc

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            arch = self.inject_fiscal_fields(arch)
        return arch, view

    @api.depends(
        "discount_value",
        "amount_tax_not_included",
        "amount_tax_withholding",
        "price_unit",
        "quantity",
        "fiscal_operation_line_id",
        "cfop_id",
        "icms_relief_value",
        "insurance_value",
        "other_value",
        "freight_value",
        "pis_value",
        "cofins_value",
        "icms_value",
        "ii_value",
        "ii_customhouse_charges",
    )
    def _compute_fiscal_amounts(self):
        for record in self:
            round_curr = record.currency_id or self.env.ref("base.BRL")

            # Total value of products or services
            record.price_gross = round_curr.round(record.price_unit * record.quantity)
            record.amount_fiscal = record.price_gross - record.discount_value
            record.fiscal_amount_tax = record.amount_tax_not_included

            add_to_amount = sum(record[a] for a in record._add_fields_to_amount())
            rm_to_amount = sum(record[r] for r in record._rm_fields_to_amount())
            record.fiscal_amount_untaxed = (
                record.price_gross
                - record.discount_value
                + add_to_amount
                - rm_to_amount
            )

            # Valor do documento (NF)
            record.fiscal_amount_total = (
                record.fiscal_amount_untaxed + record.fiscal_amount_tax
            )

            # Valor Liquido (TOTAL + IMPOSTOS - RETENÇÕES)
            record.amount_taxed = (
                record.fiscal_amount_total - record.amount_tax_withholding
            )

            # Valor do documento (NF) - RETENÇÕES
            record.fiscal_amount_total = record.amount_taxed

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

    @api.depends("tax_icms_or_issqn", "partner_id")
    def _compute_allow_csll_irpj(self):
        """Calculates the possibility of 'CSLL' and 'IRPJ' tax charges."""
        for line in self:
            # Determine if 'CSLL' and 'IRPJ' taxes may apply:
            # 1. When providing services (tax_icms_or_issqn == "issqn")
            # 2. When supplying products to public entities (partner_is_public_entity
            #  is True)
            if line.tax_icms_or_issqn == "issqn" or line.partner_is_public_entity:
                line.allow_csll_irpj = True  # Tax charges may apply
            else:
                line.allow_csll_irpj = False  # No tax charges expected

    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.line.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop("id", None)

        if default:  # in case you want to use new rather than write later
            return {f"default_{k}": vals[k] for k in vals.keys()}
        return vals

    @api.depends("fiscal_operation_id", "partner_id", "product_id")
    def _compute_fiscal_operation_line_id(self):
        for line in self:
            if line.fiscal_operation_id:
                line.fiscal_operation_line_id = (
                    line.fiscal_operation_id.line_definition(
                        company=line.company_id,
                        partner=line.partner_id,
                        product=line.product_id,
                    )
                )

    @api.depends(
        "partner_id",
        "fiscal_operation_line_id",
        "product_id",
        "ncm_id",
        "nbs_id",
        "nbm_id",
        "cest_id",
        "city_taxation_code_id",
        "service_type_id",
        "ind_final",
    )
    def _compute_fiscal_tax_ids(self):
        for line in self:
            if line.fiscal_operation_line_id:
                mapping_result = line.fiscal_operation_line_id.map_fiscal_taxes(
                    company=line.company_id,
                    partner=line._get_fiscal_partner(),
                    product=line.product_id,
                    ncm=line.ncm_id,
                    nbm=line.nbm_id,
                    nbs=line.nbs_id,
                    cest=line.cest_id,
                    city_taxation_code=line.city_taxation_code_id,
                    service_type=line.service_type_id,
                    ind_final=line.ind_final,
                )
                line.cfop_id = mapping_result["cfop"]
                line.ipi_guideline_id = mapping_result["ipi_guideline"]
                line.tax_classification_id = mapping_result["tax_classification"]
                line.icms_tax_benefit_id = mapping_result["icms_tax_benefit_id"]

                if line._is_imported():
                    continue

                taxes = line.env["l10n_br_fiscal.tax"]
                for tax in mapping_result["taxes"].values():
                    taxes |= tax
                line.fiscal_tax_ids = taxes

    @api.depends("fiscal_operation_line_id")
    def _compute_comment_ids(self):
        for line in self:
            line.comment_ids = [
                Command.set(line.fiscal_operation_line_id.comment_ids.ids)
            ]

    @api.model
    def _build_null_mask_dict(self) -> dict:
        """
        Build a null values mask dict to reset all fiscal fields.
        """
        mask_dict = {
            f[0]: False
            for f in filter(
                lambda f: f[1].compute == "_compute_tax_fields",
                self.env["l10n_br_fiscal.document.line.mixin"]._fields.items(),
            )
        }
        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            mask_dict[fiscal_tax_field] = False
        return mask_dict

    def write(self, vals):
        res = super().write(vals)

        # Verifica se algum campo de imposto relevante foi alterado no 'write'
        tax_fields_in_vals = [fld for fld in vals if fld in FISCAL_TAX_ID_FIELDS]

        if tax_fields_in_vals:
            # Por segurança, sempre recalcula se um campo relevante mudou.
            self._update_fiscal_tax_ids()

        return res

    def _update_fiscal_tax_ids(self):
        taxes = self.env["l10n_br_fiscal.tax"]
        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            taxes |= self[fiscal_tax_field]

        for line in self:
            taxes_groups = line.fiscal_tax_ids.mapped("tax_domain")
            fiscal_taxes = line.fiscal_tax_ids.filtered(
                lambda ft, taxes_groups=taxes_groups: ft.tax_domain not in taxes_groups
            )
            line.fiscal_tax_ids = fiscal_taxes + taxes

    @api.onchange(*FISCAL_TAX_ID_FIELDS)
    def _onchange_fiscal_taxes(self):
        self._update_fiscal_tax_ids()

    @api.depends(
        "partner_id",
        "fiscal_tax_ids",
        "product_id",
        "price_unit",
        "quantity",
        "uom_id",
        "fiscal_price",
        "fiscal_quantity",
        "uot_id",
        "discount_value",
        "insurance_value",
        "ii_customhouse_charges",
        "ii_iof_value",
        "other_value",
        "freight_value",
        "ncm_id",
        "nbs_id",
        "nbm_id",
        "cest_id",
        "fiscal_operation_line_id",
        "cfop_id",
        "icmssn_range_id",
        "icms_origin",
        "icms_cst_id",
        "ind_final",
        "icms_relief_id",
    )
    def _compute_tax_fields(self):
        """
        Compute base, percent, value... tax fields for ICMS, IPI, PIS, COFINS... taxes.
        """
        null_mask = None
        for line in self.filtered(lambda line: not line._is_imported()):
            if null_mask is None:
                null_mask = self._build_null_mask_dict()
            to_update = null_mask.copy()
            # prepare with default values
            to_update.update(
                {
                    "icms_base_type": ICMS_BASE_TYPE_DEFAULT,
                    "icmsst_base_type": ICMS_ST_BASE_TYPE_DEFAULT,
                    "ipi_base_type": TAX_BASE_TYPE_PERCENT,
                    "cofins_base_type": TAX_BASE_TYPE_PERCENT,
                    "cofinsst_base_type": TAX_BASE_TYPE_PERCENT,
                    "cofins_wh_base_type": TAX_BASE_TYPE_PERCENT,
                    "pis_base_type": TAX_BASE_TYPE_PERCENT,
                    "pisst_base_type": TAX_BASE_TYPE_PERCENT,
                    "pis_wh_base_type": TAX_BASE_TYPE_PERCENT,
                    "cbs_base_type": TAX_BASE_TYPE_PERCENT,
                    "ibs_base_type": TAX_BASE_TYPE_PERCENT,
                }
            )
            if line.fiscal_operation_line_id:
                compute_result = line.fiscal_tax_ids.compute_taxes(
                    company=line.company_id,
                    partner=line._get_fiscal_partner(),
                    product=line.product_id,
                    price_unit=line.price_unit,
                    quantity=line.quantity,
                    uom_id=line.uom_id,
                    fiscal_price=line.fiscal_price,
                    fiscal_quantity=line.fiscal_quantity,
                    uot_id=line.uot_id,
                    discount_value=line.discount_value,
                    insurance_value=line.insurance_value,
                    ii_customhouse_charges=line.ii_customhouse_charges,
                    ii_iof_value=line.ii_iof_value,
                    other_value=line.other_value,
                    freight_value=line.freight_value,
                    ncm=line.ncm_id,
                    nbs=line.nbs_id,
                    nbm=line.nbm_id,
                    cest=line.cest_id,
                    operation_line=line.fiscal_operation_line_id,
                    cfop=line.cfop_id,
                    icmssn_range=line.icmssn_range_id,
                    icms_origin=line.icms_origin,
                    icms_cst_id=line.icms_cst_id,
                    ind_final=line.ind_final,
                    icms_relief_id=line.icms_relief_id,
                )
                to_update.update(line._prepare_tax_fields(compute_result))
            else:
                compute_result = {}
            to_update.update(
                {
                    "amount_tax_included": compute_result.get("amount_included", 0.0),
                    "amount_tax_not_included": compute_result.get(
                        "amount_not_included", 0.0
                    ),
                    "amount_tax_withholding": compute_result.get(
                        "amount_withholding", 0.0
                    ),
                    "estimate_tax": compute_result.get("estimate_tax", 0.0),
                }
            )
            in_draft_mode = line != line._origin
            if in_draft_mode:
                line.update(to_update)
            else:
                line.write(to_update)

    def _prepare_tax_fields(self, compute_result):
        self.ensure_one()
        tax_values = {}
        if self._is_imported():
            return tax_values
        computed_taxes = compute_result.get("taxes", {})
        for tax in self.fiscal_tax_ids:
            computed_tax = computed_taxes.get(tax.tax_domain, {})
            tax_field_name = f"{tax.tax_domain}_tax_id"
            if hasattr(self, tax_field_name):
                tax_values[tax_field_name] = tax.ids[0]
                method = getattr(self, f"_prepare_fields_{tax.tax_domain}", None)
                if method and computed_tax:
                    prepared_fields = method(computed_tax)
                    if prepared_fields:
                        tax_values.update(prepared_fields)
        return tax_values

    @api.depends(
        "product_id",
        "fiscal_operation_id",
    )
    def _compute_price_unit_fiscal(self):  # OK when edited from aml?? c-> check
        for line in self:
            line.price_unit = {
                "sale_price": line.product_id.list_price,
                "cost_price": line.product_id.standard_price,
            }.get(line.fiscal_operation_id.default_price_unit, 0)

    def _get_document(self):
        self.ensure_one()
        return self.document_id

    def _get_fiscal_partner(self):
        """
        Meant to be overriden when the l10n_br_fiscal.document partner_id should not
        be the same as the sale.order, purchase.order, account.move (...) partner_id.

        (In the case of invoicing, the invoicing partner set by the user should
        get priority over any invoicing contact returned by address_get.)
        """
        self.ensure_one()
        return self.partner_id

    @api.depends("product_id")
    def _compute_product_fiscal_fields(self):
        for line in self:
            if not line.product_id:
                # reset to default values:
                line.fiscal_type = False
                line.ncm_id = False
                line.nbm_id = False
                line.tax_icms_or_issqn = TAX_DOMAIN_ICMS
                line.icms_origin = ICMS_ORIGIN_DEFAULT
                line.cest_id = False
                line.nbs_id = False
                line.fiscal_genre_id = False
                line.service_type_id = False
                line.operation_indicator_id = False
                continue
            p = line.product_id
            line.fiscal_type = p.fiscal_type
            line.ncm_id = p.ncm_id
            line.nbm_id = p.nbm_id
            line.tax_icms_or_issqn = p.tax_icms_or_issqn
            line.icms_origin = p.icms_origin
            line.cest_id = p.cest_id
            line.nbs_id = p.nbs_id
            line.fiscal_genre_id = p.fiscal_genre_id
            line.service_type_id = p.service_type_id
            line.operation_indicator_id = p.operation_indicator_id

    @api.depends("product_id")
    def _compute_city_taxation_code_id(self):
        for line in self:
            if not line.product_id:
                line.city_taxation_code_id = False
                continue
            company_city = line.company_id.city_id
            city_tax_codes = line.product_id.city_taxation_code_ids
            city_tax_code = city_tax_codes.filtered(
                lambda r, _city_id=company_city: r.city_id == _city_id
            )
            if city_tax_code:
                line.city_taxation_code_id = city_tax_code
            else:
                line.city_taxation_code_id = False

    def _prepare_fields_issqn(self, tax_dict):
        self.ensure_one()
        return {
            "issqn_base": tax_dict.get("base"),
            "issqn_percent": tax_dict.get("percent_amount"),
            "issqn_reduction": tax_dict.get("percent_reduction"),
            "issqn_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_issqn_wh(self, tax_dict):
        self.ensure_one()
        return {
            "issqn_wh_base": tax_dict.get("base"),
            "issqn_wh_percent": tax_dict.get("percent_amount"),
            "issqn_wh_reduction": tax_dict.get("percent_reduction"),
            "issqn_wh_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_csll(self, tax_dict):
        self.ensure_one()
        return {
            "csll_base": tax_dict.get("base"),
            "csll_percent": tax_dict.get("percent_amount"),
            "csll_reduction": tax_dict.get("percent_reduction"),
            "csll_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_csll_wh(self, tax_dict):
        self.ensure_one()
        return {
            "csll_wh_base": tax_dict.get("base"),
            "csll_wh_percent": tax_dict.get("percent_amount"),
            "csll_wh_reduction": tax_dict.get("percent_reduction"),
            "csll_wh_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_irpj(self, tax_dict):
        self.ensure_one()
        return {
            "irpj_base": tax_dict.get("base"),
            "irpj_percent": tax_dict.get("percent_amount"),
            "irpj_reduction": tax_dict.get("percent_reduction"),
            "irpj_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_irpj_wh(self, tax_dict):
        self.ensure_one()
        return {
            "irpj_wh_base": tax_dict.get("base"),
            "irpj_wh_percent": tax_dict.get("percent_amount"),
            "irpj_wh_reduction": tax_dict.get("percent_reduction"),
            "irpj_wh_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_inss(self, tax_dict):
        self.ensure_one()
        return {
            "inss_base": tax_dict.get("base"),
            "inss_percent": tax_dict.get("percent_amount"),
            "inss_reduction": tax_dict.get("percent_reduction"),
            "inss_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_inss_wh(self, tax_dict):
        self.ensure_one()
        return {
            "inss_wh_base": tax_dict.get("base"),
            "inss_wh_percent": tax_dict.get("percent_amount"),
            "inss_wh_reduction": tax_dict.get("percent_reduction"),
            "inss_wh_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_icms(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "icms_cst_id": cst_id,
            "icms_base_type": tax_dict.get("icms_base_type", ICMS_BASE_TYPE_DEFAULT),
            "icms_base": tax_dict.get("base", 0.0),
            "icms_percent": tax_dict.get("percent_amount", 0.0),
            "icms_reduction": tax_dict.get("percent_reduction", 0.0),
            "icms_value": tax_dict.get("tax_value", 0.0),
            "icms_origin_percent": tax_dict.get("icms_origin_perc", 0.0),
            "icms_destination_percent": tax_dict.get("icms_dest_perc", 0.0),
            "icms_sharing_percent": tax_dict.get("icms_sharing_percent", 0.0),
            "icms_destination_base": tax_dict.get("icms_dest_base", 0.0),
            "icms_origin_value": tax_dict.get("icms_origin_value", 0.0),
            "icms_destination_value": tax_dict.get("icms_dest_value", 0.0),
            "icms_relief_value": tax_dict.get("icms_relief", 0.0),
        }

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
        "icms_tax_benefit_id",
    )
    def _onchange_icms_fields(self):
        if self.icms_tax_benefit_id:
            self.icms_tax_id = self.icms_tax_benefit_id.tax_id

    @api.onchange("tax_classification_id")
    def _onchange_tax_classification_id(self):
        if self.tax_classification_id:
            self.ibs_tax_id = self.tax_classification_id.tax_ibs_id
            self.cbs_tax_id = self.tax_classification_id.tax_cbs_id

    def _prepare_fields_icmssn(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        icmssn_base = tax_dict.get("base", 0.0)
        icmssn_credit_value = tax_dict.get("tax_value", 0.0)
        simple_value = icmssn_base * self.icmssn_range_id.total_tax_percent
        simple_without_icms_value = simple_value - icmssn_credit_value
        return {
            "icms_cst_id": cst_id,
            "icmssn_base": icmssn_base,
            "icmssn_percent": tax_dict.get("percent_amount"),
            "icmssn_reduction": tax_dict.get("percent_reduction"),
            "icmssn_credit_value": icmssn_credit_value,
            "simple_value": simple_value,
            "simple_without_icms_value": simple_without_icms_value,
        }

    def _prepare_fields_icmsst(self, tax_dict):
        self.ensure_one()
        return {
            "icmsst_base_type": tax_dict.get(
                "icmsst_base_type", ICMS_ST_BASE_TYPE_DEFAULT
            ),
            "icmsst_mva_percent": tax_dict.get("icmsst_mva_percent"),
            "icmsst_percent": tax_dict.get("percent_amount"),
            "icmsst_reduction": tax_dict.get("percent_reduction"),
            "icmsst_base": tax_dict.get("base"),
            "icmsst_value": tax_dict.get("tax_value"),
        }

    def _prepare_fields_icmsfcp(self, tax_dict):
        self.ensure_one()
        return {
            "icmsfcp_base": tax_dict.get("base", 0.0),
            "icmsfcp_percent": tax_dict.get("percent_amount", 0.0),
            "icmsfcp_value": tax_dict.get("tax_value", 0.0),
        }

    def _prepare_fields_icmsfcpst(self, tax_dict):
        self.ensure_one()
        return {
            "icmsfcpst_base": self.icmsst_base,
            "icmsfcpst_percent": tax_dict.get("percent_amount", 0.0),
            "icmsfcpst_value": tax_dict.get("tax_value", 0.0),
        }

    def _prepare_fields_ipi(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "ipi_cst_id": cst_id,
            "ipi_base_type": tax_dict.get("base_type", False),
            "ipi_base": tax_dict.get("base", 0.00),
            "ipi_percent": tax_dict.get("percent_amount", 0.00),
            "ipi_reduction": tax_dict.get("percent_reduction", 0.00),
            "ipi_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_ii(self, tax_dict):
        self.ensure_one()
        return {
            "ii_base": tax_dict.get("base", 0.00),
            "ii_percent": tax_dict.get("percent_amount", 0.00),
            "ii_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_cbs(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "cbs_cst_id": cst_id,
            "cbs_base_type": tax_dict.get("base_type", False),
            "cbs_base": tax_dict.get("base", 0.00),
            "cbs_percent": tax_dict.get("percent_amount", 0.00),
            "cbs_reduction": tax_dict.get("percent_reduction", 0.00),
            "cbs_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_ibs(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "ibs_cst_id": cst_id,
            "ibs_base_type": tax_dict.get("base_type", False),
            "ibs_base": tax_dict.get("base", 0.00),
            "ibs_percent": tax_dict.get("percent_amount", 0.00),
            "ibs_reduction": tax_dict.get("percent_reduction", 0.00),
            "ibs_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_pis(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "pis_cst_id": cst_id,
            "pis_base_type": tax_dict.get("base_type"),
            "pis_base": tax_dict.get("base", 0.00),
            "pis_percent": tax_dict.get("percent_amount", 0.00),
            "pis_reduction": tax_dict.get("percent_reduction", 0.00),
            "pis_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_pis_wh(self, tax_dict):
        self.ensure_one()
        return {
            "pis_wh_base_type": tax_dict.get("base_type"),
            "pis_wh_base": tax_dict.get("base", 0.00),
            "pis_wh_percent": tax_dict.get("percent_amount", 0.00),
            "pis_wh_reduction": tax_dict.get("percent_reduction", 0.00),
            "pis_wh_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_pisst(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "pisst_cst_id": cst_id,
            "pisst_base_type": tax_dict.get("base_type"),
            "pisst_base": tax_dict.get("base", 0.00),
            "pisst_percent": tax_dict.get("percent_amount", 0.00),
            "pisst_reduction": tax_dict.get("percent_reduction", 0.00),
            "pisst_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_cofins(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "cofins_cst_id": cst_id,
            "cofins_base_type": tax_dict.get("base_type"),
            "cofins_base": tax_dict.get("base", 0.00),
            "cofins_percent": tax_dict.get("percent_amount", 0.00),
            "cofins_reduction": tax_dict.get("percent_reduction", 0.00),
            "cofins_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_cofins_wh(self, tax_dict):
        self.ensure_one()
        return {
            "cofins_wh_base_type": tax_dict.get("base_type"),
            "cofins_wh_base": tax_dict.get("base", 0.00),
            "cofins_wh_percent": tax_dict.get("percent_amount", 0.00),
            "cofins_wh_reduction": tax_dict.get("percent_reduction", 0.00),
            "cofins_wh_value": tax_dict.get("tax_value", 0.00),
        }

    def _prepare_fields_cofinsst(self, tax_dict):
        self.ensure_one()
        cst_id = tax_dict.get("cst_id").id if tax_dict.get("cst_id") else False
        return {
            "cofinsst_cst_id": cst_id,
            "cofinsst_base_type": tax_dict.get("base_type"),
            "cofinsst_base": tax_dict.get("base", 0.00),
            "cofinsst_percent": tax_dict.get("percent_amount", 0.00),
            "cofinsst_reduction": tax_dict.get("percent_reduction", 0.00),
            "cofinsst_value": tax_dict.get("tax_value", 0.00),
        }

    @api.depends("product_id", "uom_id")
    def _compute_uot_id(self):
        for line in self:
            p = line.product_id
            line.uot_id = (p.uot_id if p else False) or line.uom_id

    @api.depends("price_unit")
    def _compute_fiscal_price(self):
        for line in self:
            if line.product_id and line.price_unit:
                line.fiscal_price = line.price_unit / (
                    line.product_id.uot_factor or 1.0
                )
            else:
                line.fiscal_price = line.price_unit

    @api.depends("quantity")
    def _compute_fiscal_quantity(self):
        for line in self:
            if line.product_id and line.quantity:
                line.fiscal_quantity = line.quantity * (
                    line.product_id.uot_factor or 1.0
                )
            else:
                line.fiscal_quantity = line.quantity

    @api.model
    def _add_fields_to_amount(self):
        fields_to_amount = ["insurance_value", "other_value", "freight_value"]
        if (
            self.cfop_id.destination == CFOP_DESTINATION_EXPORT
            and self.fiscal_operation_id.fiscal_operation_type == FISCAL_IN
        ):
            fields_to_amount.append("pis_value")
            fields_to_amount.append("cofins_value")
            fields_to_amount.append("icms_value")
            fields_to_amount.append("ii_value")
            fields_to_amount.append("ii_customhouse_charges")
        return fields_to_amount

    @api.model
    def _rm_fields_to_amount(self):
        return ["icms_relief_value"]

    def _is_imported(self):
        # When the mixin is used for instance
        # in a PO line or SO line, there is no document_id
        # and we consider the document is not imported
        return hasattr(self, "document_id") and self.document_id.imported_document

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        index=True,
    )

    tax_icms_or_issqn = fields.Selection(
        selection=TAX_ICMS_OR_ISSQN,
        string="ICMS or ISSQN Tax",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    partner_is_public_entity = fields.Boolean(related="partner_id.is_public_entity")

    allow_csll_irpj = fields.Boolean(
        compute="_compute_allow_csll_irpj",
        help="Indicates potential 'CSLL' and 'IRPJ' tax charges.",
    )

    price_unit = fields.Float(
        digits="Product Price",
        store=True,
    )

    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string="Consumidor final",
        compute="_compute_ind_final",
        store=True,
        precompute=True,
        readonly=False,
    )

    def _compute_ind_final(self):
        for line in self:
            doc = line._get_document()
            if line.ind_final != doc.ind_final:
                line.ind_final = doc.ind_final

    partner_company_type = fields.Selection(related="partner_id.company_type")

    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UOM",
    )

    quantity = fields.Float(
        digits="Product Unit of Measure",
    )

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    ncm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.ncm",
        index=True,
        string="NCM",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    nbm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbm",
        index=True,
        string="NBM",
        domain="[('ncm_ids', '=', ncm_id)]",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        index=True,
        string="CEST",
        domain="[('ncm_ids', '=', ncm_id)]",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        index=True,
        string="NBS",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        domain=lambda self: self._operation_domain(),
    )

    fiscal_operation_type = fields.Selection(
        string="Operation Type",
        related="fiscal_operation_id.fiscal_operation_type",
    )

    operation_fiscal_type = fields.Selection(
        related="fiscal_operation_id.fiscal_type",
        string="Operation Fiscal Type",
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        compute="_compute_fiscal_operation_line_id",
        domain="[('fiscal_operation_id', '=', fiscal_operation_id), "
        "('state', '=', 'approved')]",
        store=True,
        precompute=True,
        readonly=False,
    )

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        domain="[('type_in_out', '=', fiscal_operation_type)]",
        compute="_compute_fiscal_tax_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    cfop_destination = fields.Selection(
        related="cfop_id.destination",
        string="CFOP Destination",
    )

    fiscal_price = fields.Float(
        digits="Product Price",
        compute="_compute_fiscal_price",
        store=True,
        precompute=True,
        readonly=False,
    )

    uot_id = fields.Many2one(
        comodel_name="uom.uom",
        string="Tax UoM",
        compute="_compute_uot_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    fiscal_quantity = fields.Float(
        digits="Product Unit of Measure",
        compute="_compute_fiscal_quantity",
        store=True,
        precompute=True,
        readonly=False,
    )

    discount_value = fields.Monetary()

    insurance_value = fields.Monetary()

    other_value = fields.Monetary()

    freight_value = fields.Monetary()

    fiscal_tax_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.tax",
        string="Fiscal Taxes",
        compute="_compute_fiscal_tax_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    amount_fiscal = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    price_gross = fields.Monetary(
        string="Gross Product/Service Amount",
        help=(
            "Total value of products or services (quantity x unit price)"
            "before any discounts."
        ),
        compute="_compute_fiscal_amounts",
    )

    fiscal_amount_untaxed = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    fiscal_amount_tax = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    amount_taxed = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    fiscal_amount_total = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    financial_total = fields.Monetary(
        string="Amount Financial",
        compute="_compute_fiscal_amounts",
    )

    financial_total_gross = fields.Monetary(
        string="Financial Gross Amount",
        help="Total amount before any discounts are applied.",
        compute="_compute_fiscal_amounts",
    )

    financial_discount_value = fields.Monetary(
        compute="_compute_fiscal_amounts",
    )

    amount_tax_included = fields.Monetary(
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    amount_tax_not_included = fields.Monetary(
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    amount_tax_withholding = fields.Monetary(
        string="Tax Withholding",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre",
        string="Fiscal Product Genre",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    fiscal_genre_code = fields.Char(
        related="fiscal_genre_id.code", string="Fiscal Product Genre Code"
    )

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type LC 166",
        domain="[('internal_type', '=', 'normal')]",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    city_taxation_code_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.city.taxation.code",
        compute="_compute_city_taxation_code_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    operation_indicator_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.indicator",
        string="Operation Indicator",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    partner_order = fields.Char(string="Partner Order (xPed)", size=15)

    partner_order_line = fields.Char(string="Partner Order Line (nItemPed)", size=6)

    # ISSQN Fields
    issqn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ISSQN",
        domain=[("tax_domain", "=", TAX_DOMAIN_ISSQN)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_fg_city_id = fields.Many2one(
        comodel_name="res.city",
        related="city_taxation_code_id.city_id",
        string="ISSQN City",
        store=True,
        precompute=True,
    )

    # vDeducao
    issqn_deduction_amount = fields.Monetary(string="ISSQN Deduction Value")

    # vOutro
    issqn_other_amount = fields.Monetary(string="ISSQN Other Value")

    # vDescIncond
    issqn_desc_incond_amount = fields.Monetary(string="ISSQN Discount Incond")

    # vDescCond
    issqn_desc_cond_amount = fields.Monetary(string="ISSQN Discount Cond")

    # indISS
    issqn_eligibility = fields.Selection(
        selection=ISSQN_ELIGIBILITY,
        string="ISSQN Eligibility",
        default=ISSQN_ELIGIBILITY_DEFAULT,
    )

    # indIncentivo
    issqn_incentive = fields.Selection(
        selection=ISSQN_INCENTIVE,
        string="ISSQN Incentive",
        default=ISSQN_INCENTIVE_DEFAULT,
    )

    issqn_base = fields.Monetary(
        string="ISSQN Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_percent = fields.Float(
        string="ISSQN %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_reduction = fields.Float(
        string="ISSQN % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_value = fields.Monetary(
        string="ISSQN Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ISSQN RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_ISSQN_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_wh_base = fields.Monetary(
        string="ISSQN RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_wh_percent = fields.Float(
        string="ISSQN RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_wh_reduction = fields.Float(
        string="ISSQN RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    issqn_wh_value = fields.Monetary(
        string="ISSQN RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS Fields
    icms_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS",
        domain=[("tax_domain", "=", TAX_DOMAIN_ICMS)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    icms_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST ICMS",
        domain="[('tax_domain', '=', {'1': 'icmssn', '2': 'icmssn', "
        "'3': 'icms'}.get(tax_framework))]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    icms_cst_code = fields.Char(
        related="icms_cst_id.code", string="ICMS CST Code", store=True
    )

    icms_tax_benefit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.definition",
        string="Tax Benefit",
        domain=[
            ("is_benefit", "=", True),
            ("tax_domain", "=", TAX_DOMAIN_ICMS),
        ],
        compute="_compute_fiscal_tax_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    icms_tax_benefit_code = fields.Char(
        string="Tax Benefit Code", related="icms_tax_benefit_id.code", store=True
    )

    icms_base_type = fields.Selection(
        selection=ICMS_BASE_TYPE,
        string="ICMS Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    icms_origin = fields.Selection(
        selection=ICMS_ORIGIN,
        string="ICMS Origin",
        compute="_compute_product_fiscal_fields",
        store=True,
        readonly=False,
        precompute=True,
    )

    # vBC - Valor da base de cálculo do ICMS
    icms_base = fields.Monetary(
        string="ICMS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pICMS - Alíquota do IMCS
    icms_percent = fields.Float(
        string="ICMS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pRedBC - Percentual de redução do ICMS
    icms_reduction = fields.Float(
        string="ICMS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vICMS - Valor do ICMS
    icms_value = fields.Monetary(
        string="ICMS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vICMSSubstituto - Valor do ICMS cobrado em operação anterior
    icms_substitute = fields.Monetary(
        string="ICMS Substitute",
        help="Valor do ICMS Próprio do Substituto cobrado em operação anterior",
    )

    # motDesICMS - Motivo da desoneração do ICMS
    icms_relief_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.icms.relief", string="ICMS Relief"
    )

    # vICMSDeson - Valor do ICMS desonerado
    icms_relief_value = fields.Monetary(
        string="ICMS Relief Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS ST Fields
    icmsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS ST",
        domain=[("tax_domain", "=", TAX_DOMAIN_ICMS_ST)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # modBCST - Modalidade de determinação da BC do ICMS ST
    icmsst_base_type = fields.Selection(
        selection=ICMS_ST_BASE_TYPE,
        string="ICMS ST Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pMVAST - Percentual da margem de valor Adicionado do ICMS ST
    icmsst_mva_percent = fields.Float(
        string="ICMS ST MVA %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pRedBCST - Percentual da Redução de BC do ICMS ST
    icmsst_reduction = fields.Float(
        string="ICMS ST % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vBCST - Valor da BC do ICMS ST
    icmsst_base = fields.Monetary(
        string="ICMS ST Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pICMSST - Alíquota do imposto do ICMS ST
    icmsst_percent = fields.Float(
        string="ICMS ST %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vICMSST - Valor do ICMS ST
    icmsst_value = fields.Monetary(
        string="ICMS ST Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vBCSTRet - Valor da base de cálculo do ICMS ST retido
    icmsst_wh_base = fields.Monetary(string="ICMS ST WH Base")

    # vICMSSTRet - Valor do IMCS ST Retido
    icmsst_wh_value = fields.Monetary(string="ICMS ST WH Value")

    # Percentagem do ICMS ST Retido anteriormente
    icmsst_wh_percent = fields.Float(string="ICMS ST WH %")

    # ICMS FCP Fields
    icmsfcp_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS FCP",
        domain=[("tax_domain", "=", TAX_DOMAIN_ICMS_FCP)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vBCFCPUFDest
    icmsfcp_base = fields.Monetary(
        string="ICMS FCP Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pFCPUFDest - Percentual do ICMS relativo ao Fundo de
    # Combate à Pobreza (FCP) na UF de destino
    icmsfcp_percent = fields.Float(
        string="ICMS FCP %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vFCPUFDest - Valor do ICMS relativo ao Fundo
    # de Combate à Pobreza (FCP) da UF de destino
    icmsfcp_value = fields.Monetary(
        string="ICMS FCP Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS FCP ST Fields
    icmsfcpst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS FCP ST",
        domain=[("tax_domain", "=", TAX_DOMAIN_ICMS_FCP_ST)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vBCFCPST
    icmsfcpst_base = fields.Monetary(
        string="ICMS FCP ST Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pFCPST - Percentual do FCP ST
    icmsfcpst_percent = fields.Float(
        string="ICMS FCP ST %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vFCPST - Valor do ICMS relativo ao
    # Fundo de Combate à Pobreza (FCP) por Substituição Tributária
    icmsfcpst_value = fields.Monetary(
        string="ICMS FCP ST Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS DIFAL Fields
    # vBCUFDest - Valor da BC do ICMS na UF de destino
    icms_destination_base = fields.Monetary(
        string="ICMS Destination Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pICMSUFDest - Alíquota interna da UF de destino
    icms_origin_percent = fields.Float(
        string="ICMS Internal %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pICMSInter - Alíquota interestadual das UF envolvidas
    icms_destination_percent = fields.Float(
        string="ICMS External %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pICMSInterPart - Percentual provisório de partilha do ICMS Interestadual
    icms_sharing_percent = fields.Float(
        string="ICMS Sharing %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vICMSUFRemet - Valor do ICMS Interestadual para a UF do remetente
    icms_origin_value = fields.Monetary(
        string="ICMS Origin Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vICMSUFDest - Valor do ICMS Interestadual para a UF de destino
    icms_destination_value = fields.Monetary(
        string="ICMS Dest. Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS Simples Nacional Fields
    icmssn_range_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.simplified.tax.range",
        string="Simplified Range Tax",
        default=_default_icmssn_range_id,
    )

    icmssn_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS SN",
        domain=[("tax_domain", "=", TAX_DOMAIN_ICMS_SN)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    icmssn_base = fields.Monetary(
        string="ICMS SN Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    icmssn_reduction = fields.Monetary(
        string="ICMS SN Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # pCredICMSSN - Alíquota aplicável de cálculo do crédito (Simples Nacional)
    icmssn_percent = fields.Float(
        string="ICMS SN %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # vCredICMSSN - Valor do crédito do ICMS que pode ser aproveitado
    icmssn_credit_value = fields.Monetary(
        string="ICMS SN Credit",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # ICMS COBRADO ANTERIORMENTE POR ST
    # vBCFCPSTRet - Valor da base de cálculo do FCP retido anteriormente
    icmsfcp_base_wh = fields.Monetary(string="FCP WH Base")

    # pFCPSTRet - Percentual do FCP retido anteriormente por ST
    icmsfcp_wh_percent = fields.Float(string="FCP WH %")

    # vFCPSTRet - Valor do FCP retido anteriormente por ST
    icmsfcp_value_wh = fields.Monetary(string="FCP WH")

    # pRedBCEfet - Percentual de redução da base de cálculo efetiva
    icms_effective_reduction = fields.Float(string="ICMS Effective % Reduction")

    # vBCEfet - Valor da base de cálculo efetiva
    icms_effective_base = fields.Monetary(string="ICMS Effective Base")

    # pICMSEfet - Alíquota do ICMS Efetiva
    icms_effective_percent = fields.Float(string="ICMS Effective %")

    # vICMSEfet - Valor do ICMS Efetivo
    icms_effective_value = fields.Monetary(string="ICMS Effective")

    # IPI Fields
    ipi_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IPI",
        domain=[("tax_domain", "=", TAX_DOMAIN_IPI)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IPI",
        domain="[('cst_type', '=', fiscal_operation_type),('tax_domain', '=', 'ipi')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_cst_code = fields.Char(
        related="ipi_cst_id.code", string="IPI CST Code", store=True
    )

    ipi_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="IPI Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_base = fields.Monetary(
        string="IPI Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_percent = fields.Float(
        string="IPI %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_reduction = fields.Float(
        string="IPI % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_value = fields.Monetary(
        string="IPI Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ipi_guideline_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline",
        string="IPI Guideline",
        domain="['|', ('cst_in_id', '=', ipi_cst_id),('cst_out_id', '=', ipi_cst_id)]",
        compute="_compute_fiscal_tax_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    # IPI Devolvido Fields
    p_devol = fields.Float(string="Percentual de mercadoria devolvida")

    ipi_devol_value = fields.Monetary(string="Valor do IPI devolvido")

    # CBS Fields
    cbs_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CBS",
        domain=(
            f"[('tax_domain', '=', '{TAX_DOMAIN_CBS}'), '|', "
            "('cst_in_id.code', 'like', cst_code_prefix_like), "
            "('cst_out_id.code', 'like', cst_code_prefix_like)]"
        ),
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST CBS",
        domain="[('cst_type', '=', fiscal_operation_type),('tax_domain', '=', 'cbs')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_cst_code = fields.Char(
        related="cbs_cst_id.code", string="CBS CST Code", store=True
    )

    cbs_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="CBS Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_base = fields.Monetary(
        string="CBS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_percent = fields.Float(
        string="CBS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_reduction = fields.Float(
        string="CBS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cbs_value = fields.Monetary(
        string="CBS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # IBS Fields
    ibs_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IBS",
        domain=(
            f"[('tax_domain', '=', '{TAX_DOMAIN_IBS}'), '|', "
            "('cst_in_id.code', 'like', cst_code_prefix_like), "
            "('cst_out_id.code', 'like', cst_code_prefix_like)]"
        ),
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IBS",
        domain="[('cst_type', '=', fiscal_operation_type),('tax_domain', '=', 'ibs')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_cst_code = fields.Char(
        related="ibs_cst_id.code", string="IBS CST Code", store=True
    )

    ibs_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="IBS Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_base = fields.Monetary(
        string="IBS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_percent = fields.Float(
        string="IBS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_reduction = fields.Float(
        string="IBS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ibs_value = fields.Monetary(
        string="IBS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # CBS/IBS Tax Classification
    tax_classification_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.classification",
        string="Tax Classification",
        compute="_compute_fiscal_tax_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    cst_code_prefix_like = fields.Char(
        compute="_compute_cst_code_prefix_like",
        help="Helper field to filter taxes by CST code prefix (3 chars) using LIKE.",
    )

    @api.depends("tax_classification_id")
    def _compute_cst_code_prefix_like(self):
        for rec in self:
            code = rec.tax_classification_id.code if rec.tax_classification_id else ""
            prefix = (code or "")[:3]
            # Avoid matching all records when the prefix is not available yet.
            rec.cst_code_prefix_like = (
                f"{prefix}%" if len(prefix) == 3 else "__no_match__%"
            )

    # II Fields
    ii_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax II",
        domain=[("tax_domain", "=", TAX_DOMAIN_II)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ii_base = fields.Monetary(
        string="II Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ii_percent = fields.Float(
        string="II %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ii_value = fields.Monetary(
        string="II Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    ii_iof_value = fields.Monetary(string="IOF Value")

    ii_customhouse_charges = fields.Monetary(string="Despesas Aduaneiras")

    # PIS/COFINS Fields
    # COFINS
    cofins_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
        "('cst_type', '=', 'all'),"
        "('tax_domain', '=', 'cofins')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_cst_code = fields.Char(
        related="cofins_cst_id.code", string="COFINS CST Code", store=True
    )

    cofins_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_base = fields.Monetary(
        string="COFINS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_percent = fields.Float(
        string="COFINS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_reduction = fields.Float(
        string="COFINS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_value = fields.Monetary(
        string="COFINS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_base_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.base", string="COFINS Base Code"
    )

    cofins_credit_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.pis.cofins.credit", string="COFINS Credit Code"
    )

    # COFINS ST
    cofinsst_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS ST",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS_ST)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS ST",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
        "('cst_type', '=', 'all'),"
        "('tax_domain', '=', 'cofinsst')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_cst_code = fields.Char(
        related="cofinsst_cst_id.code", string="COFINS ST CST Code", store=True
    )

    cofinsst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS ST Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_base = fields.Monetary(
        string="COFINS ST Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_percent = fields.Float(
        string="COFINS ST %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_reduction = fields.Float(
        string="COFINS ST % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofinsst_value = fields.Monetary(
        string="COFINS ST Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax COFINS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_COFINS_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="COFINS WH Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_base = fields.Monetary(
        string="COFINS RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_percent = fields.Float(
        string="COFINS RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_reduction = fields.Float(
        string="COFINS RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cofins_wh_value = fields.Monetary(
        string="COFINS RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # PIS
    pis_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS",
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
        "('cst_type', '=', 'all'),"
        "('tax_domain', '=', 'pis')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_cst_code = fields.Char(
        related="pis_cst_id.code", string="PIS CST Code", store=True
    )

    pis_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_base = fields.Monetary(
        string="PIS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_percent = fields.Float(
        string="PIS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_reduction = fields.Float(
        string="PIS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_value = fields.Monetary(
        string="PIS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

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
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS_ST)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS ST",
        domain="['|', ('cst_type', '=', fiscal_operation_type),"
        "('cst_type', '=', 'all'),"
        "('tax_domain', '=', 'pisst')]",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_cst_code = fields.Char(
        related="pisst_cst_id.code", string="PIS ST CST Code", store=True
    )

    pisst_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS ST Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_base = fields.Monetary(
        string="PIS ST Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_percent = fields.Float(
        string="PIS ST %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_reduction = fields.Float(
        string="PIS ST % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pisst_value = fields.Monetary(
        string="PIS ST Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax PIS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_PIS_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_base_type = fields.Selection(
        selection=TAX_BASE_TYPE,
        string="PIS WH Base Type",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_base = fields.Monetary(
        string="PIS RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_percent = fields.Float(
        string="PIS RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_reduction = fields.Float(
        string="PIS RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    pis_wh_value = fields.Monetary(
        string="PIS RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    # CSLL Fields
    csll_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CSLL",
        domain=[("tax_domain", "=", TAX_DOMAIN_CSLL)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_base = fields.Monetary(
        string="CSLL Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_percent = fields.Float(
        string="CSLL %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_reduction = fields.Float(
        string="CSLL % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_value = fields.Monetary(
        string="CSLL Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax CSLL RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_CSLL_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_wh_base = fields.Monetary(
        string="CSLL RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_wh_percent = fields.Float(
        string="CSLL RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_wh_reduction = fields.Float(
        string="CSLL RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    csll_wh_value = fields.Monetary(
        string="CSLL RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IRPJ",
        domain=[("tax_domain", "=", TAX_DOMAIN_IRPJ)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_base = fields.Monetary(
        string="IRPJ Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_percent = fields.Float(
        string="IRPJ %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_reduction = fields.Float(
        string="IRPJ % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_value = fields.Monetary(
        string="IRPJ Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax IRPJ RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_IRPJ_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_wh_base = fields.Monetary(
        string="IRPJ RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_wh_percent = fields.Float(
        string="IRPJ RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_wh_reduction = fields.Float(
        string="IRPJ RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    irpj_wh_value = fields.Monetary(
        string="IRPJ RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax INSS",
        domain=[("tax_domain", "=", TAX_DOMAIN_INSS)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_base = fields.Monetary(
        string="INSS Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_percent = fields.Float(
        string="INSS %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_reduction = fields.Float(
        string="INSS % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_value = fields.Monetary(
        string="INSS Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_wh_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax INSS RET",
        domain=[("tax_domain", "=", TAX_DOMAIN_INSS_WH)],
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_wh_base = fields.Monetary(
        string="INSS RET Base",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_wh_percent = fields.Float(
        string="INSS RET %",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_wh_reduction = fields.Float(
        string="INSS RET % Reduction",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    inss_wh_value = fields.Monetary(
        string="INSS RET Value",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    simple_value = fields.Monetary(
        string="National Simple Taxes",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    simple_without_icms_value = fields.Monetary(
        string="National Simple Taxes without ICMS",
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        string="Comments",
        domain=[("object", "=", FISCAL_COMMENT_LINE)],
        compute="_compute_comment_ids",
        store=True,
        precompute=True,
        readonly=False,
    )

    manual_additional_data = fields.Text(
        help="Additional data manually entered by user"
    )

    estimate_tax = fields.Monetary(
        compute="_compute_tax_fields",
        store=True,
        precompute=True,
        readonly=False,
    )

    cnae_id = fields.Many2one(
        related="city_taxation_code_id.cnae_id",
        comodel_name="l10n_br_fiscal.cnae",
        string="CNAE Code",
        store=True,
        precompute=True,
        readonly=False,
    )

    @api.depends("company_id")
    def _compute_currency_id(self):
        for doc_line in self:
            doc_line.currency_id = doc_line.company_id.currency_id or self.env.ref(
                "base.BRL"
            )
