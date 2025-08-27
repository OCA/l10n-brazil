# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from copy import deepcopy

from lxml import etree

from odoo import Command, api, models

from ..constants.fiscal import CFOP_DESTINATION_EXPORT, FISCAL_IN
from ..constants.icms import ICMS_BASE_TYPE_DEFAULT, ICMS_ST_BASE_TYPE_DEFAULT

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
    "icmsfcpst_tax_id",
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
                        if fiscal_node.attrib["name"] in existing_fields:
                            continue
                        field = deepcopy(fiscal_node)
                        if not field.attrib.get("optional"):
                            field.attrib["invisible"] = "0"
                            field.attrib["optional"] = "hide"
                        target_node.append(field)
        return doc

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "form":
            arch = self.inject_fiscal_fields(arch)
        return arch, view

    @api.depends(
        "fiscal_price",
        "discount_value",
        "insurance_value",
        "other_value",
        "freight_value",
        "fiscal_quantity",
        "amount_tax_not_included",
        "amount_tax_included",
        "amount_tax_withholding",
        "uot_id",
        "product_id",
        "partner_id",
        "company_id",
        "price_unit",
        "quantity",
        "icms_relief_id",
        "fiscal_operation_line_id",
    )
    def _compute_fiscal_amounts(self):
        for record in self:
            round_curr = record.currency_id or self.env.ref("base.BRL")

            # Total value of products or services
            record.price_gross = round_curr.round(record.price_unit * record.quantity)
            record.amount_fiscal = record.price_gross - record.discount_value
            record.amount_tax = record.amount_tax_not_included

            add_to_amount = sum(record[a] for a in record._add_fields_to_amount())
            rm_to_amount = sum(record[r] for r in record._rm_fields_to_amount())
            record.amount_untaxed = (
                record.price_gross
                - record.discount_value
                + add_to_amount
                - rm_to_amount
            )

            # Valor do documento (NF)
            record.amount_total = record.amount_untaxed + record.amount_tax

            # Valor Liquido (TOTAL + IMPOSTOS - RETENÇÕES)
            record.amount_taxed = record.amount_total - record.amount_tax_withholding

            # Valor do documento (NF) - RETENÇÕES
            record.amount_total = record.amount_taxed

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

    @api.depends("tax_icms_or_issqn", "partner_is_public_entity")
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

    @api.onchange("fiscal_operation_id", "company_id", "partner_id", "product_id")
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.fiscal_operation_line_id = self.fiscal_operation_id.line_definition(
                company=self.company_id,
                partner=self._get_fiscal_partner(),
                product=self.product_id,
            )

    def _get_fiscal_tax_ids_dependencies(self):
        """
        Dynamically get the list of fields dependencies, overriden in l10n_br_purchase.
        """
        return [
            "company_id",
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
        ]

    @api.depends(lambda self: self._get_fiscal_tax_ids_dependencies())
    def _compute_fiscal_tax_ids(self):
        """
        Use fiscal_operation_line_id to map and compute the applicable Brazilian taxes.

        Among the dependencies, company_id, partner_id and ind_final are related
        to the fiscal document/line container. When called from account.move.line
        via _inherits on newID records, we read these values from the related aml
        to work around and _inherits/precompute limitation.
        """
        if self._context.get("skip_compute_fiscal_tax_ids"):
            return
        for line in self:
            if hasattr(line, "account_line_ids") and line.account_line_ids:
                # it seems Odoo 16 ORM has a limitation when line is an
                # l10n_br_fiscal.document.line that is edited via an account.move.line
                # form and when both are a newID, then line relational field might be
                # empty here. But in this case, we detect it and we wrap it back in the
                wrapped_line = line.account_line_ids[0]
            else:
                wrapped_line = line

            if wrapped_line.fiscal_operation_line_id:
                mapping_result = wrapped_line.fiscal_operation_line_id.map_fiscal_taxes(
                    company=wrapped_line.company_id,
                    partner=wrapped_line._get_fiscal_partner(),
                    product=wrapped_line.product_id,
                    ncm=wrapped_line.ncm_id,
                    nbm=wrapped_line.nbm_id,
                    nbs=wrapped_line.nbs_id,
                    cest=wrapped_line.cest_id,
                    city_taxation_code=wrapped_line.city_taxation_code_id,
                    service_type=wrapped_line.service_type_id,
                    ind_final=wrapped_line.ind_final,
                )
                line.cfop_id = mapping_result["cfop"]
                line.ipi_guideline_id = mapping_result["ipi_guideline"]
                line.icms_tax_benefit_id = mapping_result["icms_tax_benefit_id"]
                if wrapped_line._is_imported():
                    return

                taxes = line.env["l10n_br_fiscal.tax"]
                for tax in mapping_result["taxes"].values():
                    taxes |= tax
                line.fiscal_tax_ids = taxes
                line.comment_ids = line.fiscal_operation_line_id.comment_ids

            else:
                line.fiscal_tax_ids = [Command.clear()]

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

    def _get_tax_fields_dependencies(self):
        """
        Dynamically get the list of fields dependencies, overriden in l10n_br_purchase.
        """
        # IMPORTANT NOTE: as _compute_fiscal_tax_ids triggers _compute_tax_fields,
        # we don't put fields that trigger _compute_fiscal_tax_ids as dependencies here.
        return [
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
            "cfop_id",
            "icmssn_range_id",
            "icms_origin",
            "icms_cst_id",
            "icms_relief_id",
            "fiscal_tax_ids",
        ]

    @api.depends(lambda self: self._get_tax_fields_dependencies())
    def _compute_tax_fields(self):
        """
        Compute base, percent, value... tax fields for ICMS, IPI, PIS, COFINS... taxes.
        """
        if self._context.get("skip_compute_tax_fields"):
            return

        null_mask = None
        for line in self.filtered(lambda line: not line._is_imported()):
            if hasattr(line, "account_line_ids") and line.account_line_ids:
                # it seems Odoo 16 ORM has a limitation when line is an
                # l10n_br_fiscal.document.line that is edited via an account.move.line
                # form and when both are a newID, then line relational field might be
                # empty here. But in this case, we detect it and we wrap it back in the
                wrapped_line = line.account_line_ids[0]
            else:
                wrapped_line = line

            if null_mask is None:
                null_mask = self._build_null_mask_dict()
            to_update = null_mask.copy()
            if wrapped_line.fiscal_operation_line_id:
                compute_result = wrapped_line.fiscal_tax_ids.compute_taxes(
                    company=wrapped_line.company_id,
                    partner=wrapped_line._get_fiscal_partner(),
                    product=wrapped_line.product_id,
                    price_unit=wrapped_line.price_unit,
                    quantity=wrapped_line.quantity,
                    uom_id=wrapped_line.uom_id,
                    fiscal_price=wrapped_line.fiscal_price,
                    fiscal_quantity=wrapped_line.fiscal_quantity,
                    uot_id=wrapped_line.uot_id,
                    discount_value=wrapped_line.discount_value,
                    insurance_value=wrapped_line.insurance_value,
                    ii_customhouse_charges=wrapped_line.ii_customhouse_charges,
                    ii_iof_value=wrapped_line.ii_iof_value,
                    other_value=wrapped_line.other_value,
                    freight_value=wrapped_line.freight_value,
                    ncm=wrapped_line.ncm_id,
                    nbs=wrapped_line.nbs_id,
                    nbm=wrapped_line.nbm_id,
                    cest=wrapped_line.cest_id,
                    operation_line=wrapped_line.fiscal_operation_line_id,
                    cfop=wrapped_line.cfop_id,
                    icmssn_range=wrapped_line.icmssn_range_id,
                    icms_origin=wrapped_line.icms_origin,
                    icms_cst_id=wrapped_line.icms_cst_id,
                    ind_final=wrapped_line.ind_final,
                    icms_relief_id=wrapped_line.icms_relief_id,
                )
                to_update.update(wrapped_line._prepare_tax_fields(compute_result))
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
            in_draft_mode = wrapped_line != wrapped_line._origin
            if in_draft_mode:
                wrapped_line.update(to_update)
            else:
                wrapped_line.write(to_update)

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

    def __document_comment_vals(self):
        self.ensure_one()
        return {
            "user": self.env.user,
            "ctx": self._context,
            "doc": self.document_id if hasattr(self, "document_id") else None,
            "item": self,
        }

    def _document_comment(self):
        for d in self:
            d.additional_data = d.comment_ids.compute_message(
                d.__document_comment_vals(), d.manual_additional_data
            )

    def _get_fiscal_partner(self):
        """
        Meant to be overriden when the l10n_br_fiscal.document partner_id should not
        be the same as the sale.order, purchase.order, account.move (...) partner_id.

        (In the case of invoicing, the invoicing partner set by the user should
        get priority over any invoicing contact returned by address_get.)
        """
        self.ensure_one()
        return self.partner_id

    @api.onchange("product_id")
    def _onchange_product_id_fiscal(self):
        if not self.fiscal_operation_id:
            return
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

        self._compute_price_unit_fiscal()
        self._onchange_fiscal_operation_id()

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

    @api.onchange(*FISCAL_TAX_ID_FIELDS)
    def _onchange_fiscal_taxes(self):
        taxes = self.env["l10n_br_fiscal.tax"]
        for fiscal_tax_field in FISCAL_TAX_ID_FIELDS:
            taxes |= self[fiscal_tax_field]

        for line in self:
            taxes_groups = line.fiscal_tax_ids.mapped("tax_domain")
            fiscal_taxes = line.fiscal_tax_ids.filtered(
                lambda ft, taxes_groups=taxes_groups: ft.tax_domain not in taxes_groups
            )
            line.fiscal_tax_ids = fiscal_taxes + taxes

    @api.depends("uom_id")
    def _compute_uot_id(self):
        for line in self:
            if not line.uot_id:
                line.uot_id = line.uom_id

    @api.onchange("price_unit")
    def _onchange_price_unit_fiscal(self):
        self.fiscal_price = 0
        self._compute_fiscal_price()

    @api.depends("price_unit")
    def _compute_fiscal_price(self):
        for line in self:
            # this test and the onchange are required to avoid
            # resetting manual changes in fiscal_price
            if not line.fiscal_price:
                if line.product_id and line.price_unit:
                    line.fiscal_price = line.price_unit / (
                        line.product_id.uot_factor or 1.0
                    )
                else:
                    line.fiscal_price = line.price_unit

    @api.onchange("quantity")
    def _onchange_quantity_fiscal(self):
        self.fiscal_quantity = 0
        self._compute_fiscal_quantity()

    @api.depends("quantity")
    def _compute_fiscal_quantity(self):
        for line in self:
            # this test and the onchange are required to avoid
            # resetting manual changes in fiscal_quantity
            if not line.fiscal_quantity:
                if line.product_id and line.quantity:
                    line.fiscal_quantity = line.quantity * (
                        line.product_id.uot_factor or 1.0
                    )
                else:
                    line.fiscal_quantity = line.quantity

    @api.onchange("city_taxation_code_id")
    def _onchange_city_taxation_code_id(self):
        if self.city_taxation_code_id:
            self.cnae_id = self.city_taxation_code_id.cnae_id
            self._onchange_fiscal_operation_id()
            if self.city_taxation_code_id.city_id:
                self.update({"issqn_fg_city_id": self.city_taxation_code_id.city_id})

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
