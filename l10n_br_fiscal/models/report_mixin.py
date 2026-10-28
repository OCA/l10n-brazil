# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml.builder import E

from odoo import _, api, fields, models

from ..constants.fiscal import (
    CFOP_DESTINATION,
    CFOP_DESTINATION_EXPORT,
    CFOP_DESTINATION_EXTERNAL,
    CFOP_DESTINATION_INTERNAL,
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    FINAL_CUSTOMER,
    FINAL_CUSTOMER_YES,
    FISCAL_IN,
    FISCAL_IN_OUT_ALL,
    FISCAL_OUT,
    PRODUCT_FISCAL_TYPE,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ISSQN,
    TAX_ICMS_OR_ISSQN,
)
from ..constants.icms import ICMS_ORIGIN

FISCAL_REPORT_FILTERS = "l10n_br_fiscal_report_filters"

EDOC_VOID_STATES = [
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_INUTILIZADA,
]


class FiscalReportFilterMixin(models.AbstractModel):
    """Standard fiscal filters for search views.

    A search view gets them by declaring the placeholder
    ``<separator name="l10n_br_fiscal_report_filters"/>``. The fiscal document
    and document line mixins inherit it, so it works on the analysis reports
    and on every model with fiscal fields (orders, invoices, pickings...).
    Only the filters the model supports are injected.
    """

    _name = "l10n_br_fiscal.report.filter.mixin"
    _description = "Fiscal Report Filter Mixin"

    @api.model
    def _fiscal_report_filters(self):
        """Filters as dicts, None stands for a separator.

        - ``domains``: alternatives, the first one whose fields the model can
          search is used (line fields first, then the document totals);
        - ``requires``: fields the model must have to show the filter.
        """
        return [
            {
                "name": "out",
                "label": _("Outgoing"),
                "domains": [[("fiscal_operation_type", "=", FISCAL_OUT)]],
            },
            {
                "name": "in",
                "label": _("Incoming"),
                "domains": [[("fiscal_operation_type", "=", FISCAL_IN)]],
            },
            None,
            {
                "name": "cfop_internal",
                "label": _("Internal Operation"),
                "domains": [[("cfop_destination", "=", CFOP_DESTINATION_INTERNAL)]],
            },
            {
                "name": "cfop_interstate",
                "label": _("Interstate Operation"),
                "domains": [[("cfop_destination", "=", CFOP_DESTINATION_EXTERNAL)]],
            },
            {
                "name": "cfop_foreign",
                "label": _("Foreign Operation"),
                "domains": [[("cfop_destination", "=", CFOP_DESTINATION_EXPORT)]],
            },
            None,
            {
                "name": "final_customer",
                "label": _("Final Customer"),
                "domains": [[("ind_final", "=", FINAL_CUSTOMER_YES)]],
            },
            # own block: filters of the same block are combined with OR
            None,
            {
                "name": "products",
                "label": _("Products (ICMS)"),
                "domains": [[("tax_icms_or_issqn", "=", TAX_DOMAIN_ICMS)]],
            },
            {
                "name": "services",
                "label": _("Services (ISSQN)"),
                "domains": [[("tax_icms_or_issqn", "=", TAX_DOMAIN_ISSQN)]],
            },
            None,
            {
                "name": "with_icmsst",
                "label": _("With ICMS ST"),
                "domains": [
                    [("icmsst_value", "!=", 0)],
                    [("amount_icmsst_value", "!=", 0)],
                ],
            },
            {
                "name": "with_difal",
                "label": _("With ICMS DIFAL"),
                "domains": [
                    [("icms_destination_value", "!=", 0)],
                    [("amount_icms_destination_value", "!=", 0)],
                ],
            },
            {
                "name": "with_ipi",
                "label": _("With IPI"),
                "domains": [
                    [("ipi_value", "!=", 0)],
                    [("amount_ipi_value", "!=", 0)],
                ],
            },
            {
                "name": "with_withholding",
                "label": _("With Withholdings"),
                "domains": [[("amount_tax_withholding", "!=", 0)]],
            },
            {
                "name": "with_cbs_ibs",
                "label": _("With CBS/IBS"),
                "domains": [
                    ["|", ("cbs_value", "!=", 0), ("ibs_value", "!=", 0)],
                    ["|", ("amount_cbs_value", "!=", 0), ("amount_ibs_value", "!=", 0)],
                ],
            },
            None,
            {
                "name": "issuer_company",
                "label": _("Own Issue"),
                "domains": [[("issuer", "=", DOCUMENT_ISSUER_COMPANY)]],
                "requires": ["state_edoc"],
            },
            {
                "name": "issuer_partner",
                "label": _("Third-party Issue"),
                "domains": [[("issuer", "=", DOCUMENT_ISSUER_PARTNER)]],
                "requires": ["state_edoc"],
            },
            None,
            {
                "name": "edoc_not_void",
                "label": _("Not Cancelled"),
                "domains": [[("state_edoc", "not in", EDOC_VOID_STATES)]],
            },
            {
                "name": "edoc_void",
                "label": _("Cancelled, Denied or Voided"),
                "domains": [[("state_edoc", "in", EDOC_VOID_STATES)]],
            },
        ]

    @api.model
    def _fiscal_report_groupbys(self):
        """Group bys as (field, required fields)."""
        return [
            ("fiscal_operation_id", []),
            ("fiscal_operation_line_id", []),
            ("cfop_id", []),
            ("cfop_destination", []),
            ("ncm_id", []),
            ("fiscal_type", []),
            ("icms_cst_id", []),
            ("partner_state_id", []),
            ("tax_classification_id", []),
            ("document_type_id", []),
            ("issuer", ["state_edoc"]),
            ("state_edoc", []),
        ]

    @api.model
    def _fiscal_report_searchable(self, fname):
        field = self._fields.get(fname)
        return bool(field and (field.store or field.related or field.search))

    @api.model
    def _fiscal_report_domain(self, item):
        """The first domain of the filter the model can search, or None."""
        if not all(fname in self._fields for fname in item.get("requires", [])):
            return None
        for domain in item["domains"]:
            leaves = [leaf for leaf in domain if len(leaf) == 3]
            if all(self._fiscal_report_searchable(leaf[0]) for leaf in leaves):
                return domain
        return None

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == "search":
            for node in arch.xpath(f"//separator[@name='{FISCAL_REPORT_FILTERS}']"):
                self._inject_fiscal_report_filters(node)
        return arch, view

    @api.model
    def _inject_fiscal_report_filters(self, placeholder):
        nodes = [E.separator()]
        for item in self._fiscal_report_filters():
            if item is None:
                if nodes[-1].tag != "separator":
                    nodes.append(E.separator())
                continue
            domain = self._fiscal_report_domain(item)
            if domain is not None:
                nodes.append(
                    E.filter(
                        name=f"fiscal_{item['name']}",
                        string=item["label"],
                        domain=repr(domain),
                    )
                )
        group = E.group(expand="0", string=_("Fiscal"))
        for fname, requires in self._fiscal_report_groupbys():
            # only stored fields can be grouped (e.g. not the related ones
            # of stock.move nor the fields delegated to account.move)
            field = self._fields.get(fname)
            if field and field.store and all(r in self._fields for r in requires):
                group.append(
                    E.filter(
                        name=f"fiscal_groupby_{fname}",
                        string=field._description_string(self.env),
                        context=repr({"group_by": fname}),
                    )
                )
        nodes.append(group)
        parent = placeholder.getparent()
        index = parent.index(placeholder)
        parent.remove(placeholder)
        for offset, node in enumerate(nodes):
            parent.insert(index + offset, node)


class FiscalReportMixin(models.AbstractModel):
    """Fiscal dimensions and measures for the SQL analysis reports.

    The report declares the fields once and builds the SQL from the aliases
    each report uses, so sale.report, purchase.report, account.invoice.report
    and the fiscal document line analysis expose the same fiscal data.
    """

    _name = "l10n_br_fiscal.report.mixin"
    _inherit = "l10n_br_fiscal.report.filter.mixin"
    _description = "Fiscal Report Mixin"

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        readonly=True,
    )

    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Fiscal Operation Line",
        readonly=True,
    )

    fiscal_operation_type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        readonly=True,
    )

    cfop_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP",
        readonly=True,
    )

    cfop_destination = fields.Selection(
        selection=CFOP_DESTINATION,
        string="CFOP Destination",
        readonly=True,
    )

    ncm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.ncm",
        string="NCM",
        readonly=True,
    )

    nbm_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbm",
        string="NBM",
        readonly=True,
    )

    cest_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cest",
        string="CEST",
        readonly=True,
    )

    nbs_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.nbs",
        string="NBS",
        readonly=True,
    )

    fiscal_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE,
        string="Product Fiscal Type",
        readonly=True,
    )

    fiscal_genre_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.product.genre",
        string="Fiscal Product Genre",
        readonly=True,
    )

    service_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.service.type",
        string="Service Type",
        readonly=True,
    )

    icms_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST ICMS",
        readonly=True,
    )

    icms_origin = fields.Selection(
        selection=ICMS_ORIGIN,
        string="ICMS Origin",
        readonly=True,
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string="Final Customer",
        readonly=True,
    )

    tax_icms_or_issqn = fields.Selection(
        selection=TAX_ICMS_OR_ISSQN,
        string="ICMS or ISSQN Tax",
        readonly=True,
    )

    tax_classification_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.classification",
        string="Tax Classification",
        readonly=True,
    )

    partner_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Partner State",
        readonly=True,
    )

    discount_value = fields.Float(digits="Account")

    freight_value = fields.Float(digits="Account")

    insurance_value = fields.Float(digits="Account")

    other_value = fields.Float(string="Other Costs", digits="Account")

    icms_base = fields.Float(string="ICMS Base", digits="Account")

    icms_value = fields.Float(string="ICMS Value", digits="Account")

    icmsst_base = fields.Float(string="ICMS ST Base", digits="Account")

    icmsst_value = fields.Float(string="ICMS ST Value", digits="Account")

    icmsfcp_value = fields.Float(string="ICMS FCP Value", digits="Account")

    icmsfcpst_value = fields.Float(string="ICMS FCP ST Value", digits="Account")

    icms_origin_value = fields.Float(string="ICMS DIFAL Origin Value", digits="Account")

    icms_destination_value = fields.Float(
        string="ICMS DIFAL Destination Value", digits="Account"
    )

    ipi_base = fields.Float(string="IPI Base", digits="Account")

    ipi_value = fields.Float(string="IPI Value", digits="Account")

    pis_value = fields.Float(string="PIS Value", digits="Account")

    cofins_value = fields.Float(string="COFINS Value", digits="Account")

    issqn_value = fields.Float(string="ISSQN Value", digits="Account")

    ii_value = fields.Float(string="II Value", digits="Account")

    cbs_value = fields.Float(string="CBS Value", digits="Account")

    ibs_value = fields.Float(string="IBS Value", digits="Account")

    amount_tax_included = fields.Float(
        string="Taxes Included in Price", digits="Account"
    )

    amount_tax_not_included = fields.Float(
        string="Taxes Not Included in Price", digits="Account"
    )

    amount_tax_withholding = fields.Float(string="Tax Withholdings", digits="Account")

    estimate_tax = fields.Float(string="Estimated Taxes (IBPT)", digits="Account")

    @api.model
    def _fiscal_report_measures(self):
        """Measures read from the fiscal line columns with the same name."""
        return [
            "discount_value",
            "freight_value",
            "insurance_value",
            "other_value",
            "icms_base",
            "icms_value",
            "icmsst_base",
            "icmsst_value",
            "icmsfcp_value",
            "icmsfcpst_value",
            "icms_origin_value",
            "icms_destination_value",
            "ipi_base",
            "ipi_value",
            "pis_value",
            "cofins_value",
            "issqn_value",
            "ii_value",
            "cbs_value",
            "ibs_value",
            "amount_tax_included",
            "amount_tax_not_included",
            "amount_tax_withholding",
            "estimate_tax",
        ]

    @api.model
    def _fiscal_report_dimensions(self, line, partner):
        """Mapping field -> SQL expression of the fiscal dimensions.

        :param line: alias of the table with the fiscal line columns
        :param partner: alias of the res_partner giving the partner state
        """
        res = {
            fname: f"{line}.{fname}"
            for fname in (
                "fiscal_operation_id",
                "fiscal_operation_line_id",
                "cfop_id",
                "ncm_id",
                "nbm_id",
                "cest_id",
                "nbs_id",
                "fiscal_type",
                "fiscal_genre_id",
                "service_type_id",
                "icms_cst_id",
                "icms_origin",
                "ind_final",
                "tax_icms_or_issqn",
                "tax_classification_id",
            )
        }
        res.update(
            {
                "fiscal_operation_type": (
                    "fiscal_report_operation.fiscal_operation_type"
                ),
                "cfop_destination": "fiscal_report_cfop.destination",
                "partner_state_id": f"{partner}.state_id",
            }
        )
        return res

    @api.model
    def _fiscal_report_select(self, line, partner, factor="1", aggregate=True):
        """Mapping field -> SQL expression of all the fiscal report fields.

        :param factor: SQL expression applied to the measures (sign, currency)
        :param aggregate: wrap the measures in SUM() for GROUP BY reports
        """
        res = self._fiscal_report_dimensions(line, partner)
        for fname in self._fiscal_report_measures():
            expr = f"COALESCE({line}.{fname}, 0) * {factor}"
            res[fname] = f"SUM({expr})" if aggregate else expr
        return res

    @api.model
    def _fiscal_report_from(self, line):
        """Joins needed by the fiscal dimensions."""
        return f"""
            LEFT JOIN l10n_br_fiscal_operation fiscal_report_operation
                ON fiscal_report_operation.id = {line}.fiscal_operation_id
            LEFT JOIN l10n_br_fiscal_cfop fiscal_report_cfop
                ON fiscal_report_cfop.id = {line}.cfop_id
        """

    @api.model
    def _fiscal_report_group_by(self, line, partner):
        return ", ".join(self._fiscal_report_dimensions(line, partner).values())
