# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from copy import deepcopy

from lxml import etree
from lxml.builder import E

from odoo import Command, api, models

from ..constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    FISCAL_IN,
    FISCAL_TAX_ID_FIELDS,
    TAX_BASE_TYPE_PERCENT,
    TAX_DOMAIN_ICMS,
)
from ..constants.icms import (
    ICMS_BASE_TYPE_DEFAULT,
    ICMS_ORIGIN_DEFAULT,
    ICMS_ST_BASE_TYPE_DEFAULT,
)


class FiscalDocumentLineMixinMethods(models.AbstractModel):
    """
    Provides the method implementations for l10n_br_fiscal.document.line.mixin.

    These methods are extracted into this separate mixin due to the way
    l10n_br_fiscal.document.line is incorporated into account.move.line
    by the l10n_br_account module (decorator pattern).

    Specifically:
    - In l10n_br_account, fields from l10n_br_fiscal.document.line
      are added to account.move.line using Odoo's `_inherits` (composition)
      mechanism.
    - The methods in *this* mixin, however, are intended to be inherited
      using the standard `_inherit` mechanism.

    This separation is crucial because `_inherits` handles field composition
    but does not inherit methods. Thus, `_inherit` is used to bring in
    these methods. If these methods were defined in the same class as the
    fields of l10n_br_fiscal.document.line.mixin (which are subject to
    `_inherits`), and account.move.line also used `_inherit` on that
    single class, the fields would be duplicated.
    """

    _name = "l10n_br_fiscal.document.line.mixin.methods"
    _description = "Fiscal Document Mixin Methods"

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
