# Copyright (C) 2026-Today - KMEE (<https://kmee.com.br>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    DOCUMENT_ISSUER,
    FISCAL_IN,
    SITUACAO_EDOC,
)


class FiscalDocumentLineReport(models.Model):
    """Fiscal document lines analysis, one row per line.

    Values are positive: the fiscal operation type tells incoming from
    outgoing documents, as in the fiscal books.
    """

    _name = "l10n_br_fiscal.document.line.report"
    _inherit = "l10n_br_fiscal.report.mixin"
    _description = "Fiscal Document Lines Analysis"
    _auto = False
    _rec_name = "document_id"
    _order = "date desc, id desc"

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Fiscal Document",
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        readonly=True,
    )

    date = fields.Datetime(string="Document Date", readonly=True)

    date_in_out = fields.Datetime(string="Date In/Out", readonly=True)

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Type",
        readonly=True,
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        string="Document Serie",
        readonly=True,
    )

    issuer = fields.Selection(selection=DOCUMENT_ISSUER, readonly=True)

    state_edoc = fields.Selection(
        selection=SITUACAO_EDOC,
        string="Situation",
        readonly=True,
    )

    issqn_fg_city_id = fields.Many2one(
        comodel_name="res.city",
        string="ISSQN City",
        readonly=True,
    )

    icms_rate = fields.Char(string="ICMS Rate", readonly=True)

    ipi_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IPI",
        readonly=True,
    )

    pis_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST PIS",
        readonly=True,
    )

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        readonly=True,
    )

    cbs_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST CBS",
        readonly=True,
    )

    ibs_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST IBS",
        readonly=True,
    )

    quantity = fields.Float(digits="Product Unit of Measure", readonly=True)

    amount_gross = fields.Float(string="Gross Amount", digits="Account")

    amount_untaxed = fields.Float(string="Untaxed Amount", digits="Account")

    amount_total = fields.Float(string="Document Total", digits="Account")

    icms_relief_value = fields.Float(string="ICMS Relief Value", digits="Account")

    icmssn_credit_value = fields.Float(string="ICMS SN Credit Value", digits="Account")

    pis_base = fields.Float(string="PIS Base", digits="Account")

    cofins_base = fields.Float(string="COFINS Base", digits="Account")

    issqn_base = fields.Float(string="ISSQN Base", digits="Account")

    cbs_base = fields.Float(string="CBS Base", digits="Account")

    ibs_base = fields.Float(string="IBS Base", digits="Account")

    pis_wh_value = fields.Float(string="PIS Withholding", digits="Account")

    cofins_wh_value = fields.Float(string="COFINS Withholding", digits="Account")

    csll_wh_value = fields.Float(string="CSLL Withholding", digits="Account")

    irpj_wh_value = fields.Float(string="IRPJ Withholding", digits="Account")

    inss_wh_value = fields.Float(string="INSS Withholding", digits="Account")

    issqn_wh_value = fields.Float(string="ISSQN Withholding", digits="Account")

    @api.model
    def _fiscal_report_measures(self):
        return super()._fiscal_report_measures() + [
            "quantity",
            "icms_relief_value",
            "icmssn_credit_value",
            "pis_base",
            "cofins_base",
            "issqn_base",
            "cbs_base",
            "ibs_base",
            "pis_wh_value",
            "cofins_wh_value",
            "csll_wh_value",
            "irpj_wh_value",
            "inss_wh_value",
            "issqn_wh_value",
        ]

    @api.model
    def _select(self):
        res = {
            "id": "dl.id",
            "document_id": "dl.document_id",
            "company_id": "doc.company_id",
            "partner_id": "doc.partner_id",
            "product_id": "dl.product_id",
            "date": "doc.document_date",
            "date_in_out": "doc.date_in_out",
            "document_type_id": "doc.document_type_id",
            "document_serie_id": "doc.document_serie_id",
            "issuer": "doc.issuer",
            "state_edoc": "doc.state_edoc",
            "issqn_fg_city_id": "dl.issqn_fg_city_id",
            "icms_rate": "to_char(dl.icms_percent, 'FM990.00')",
            "ipi_cst_id": "dl.ipi_cst_id",
            "pis_cst_id": "dl.pis_cst_id",
            "cofins_cst_id": "dl.cofins_cst_id",
            "cbs_cst_id": "dl.cbs_cst_id",
            "ibs_cst_id": "dl.ibs_cst_id",
        }
        res.update(self._fiscal_report_select("dl", "partner", aggregate=False))
        # the document keeps the type also when the line has no operation
        res["fiscal_operation_type"] = (
            "COALESCE(doc.fiscal_operation_type,"
            " fiscal_report_operation.fiscal_operation_type)"
        )
        res.update(self._select_amounts())
        return ",\n".join(f"{expr} AS {fname}" for fname, expr in res.items())

    @api.model
    def _select_amounts(self):
        """Document amounts, as computed by the line mixin
        (``_compute_fiscal_amounts`` and ``_add_fields_to_amount``)."""
        gross = (
            "ROUND((COALESCE(dl.price_unit, 0)"
            " * COALESCE(dl.quantity, 0))::numeric, 2)"
        )
        imported = f"""
            CASE WHEN fiscal_report_cfop.destination = '{CFOP_DESTINATION_EXPORT}'
                AND fiscal_report_operation.fiscal_operation_type = '{FISCAL_IN}'
            THEN COALESCE(dl.pis_value, 0) + COALESCE(dl.cofins_value, 0)
                + COALESCE(dl.icms_value, 0) + COALESCE(dl.ii_value, 0)
                + COALESCE(dl.ii_customhouse_charges, 0)
            ELSE 0 END
        """
        untaxed = f"""
            {gross} - COALESCE(dl.discount_value, 0)
            + COALESCE(dl.insurance_value, 0) + COALESCE(dl.other_value, 0)
            + COALESCE(dl.freight_value, 0) - COALESCE(dl.icms_relief_value, 0)
            + {imported}
        """
        return {
            "amount_gross": gross,
            "amount_untaxed": untaxed,
            "amount_total": (f"{untaxed} + COALESCE(dl.amount_tax_not_included, 0)"),
        }

    @api.model
    def _from(self):
        return f"""
            l10n_br_fiscal_document_line dl
            JOIN l10n_br_fiscal_document doc ON doc.id = dl.document_id
            LEFT JOIN res_partner partner ON partner.id = doc.partner_id
            {self._fiscal_report_from("dl")}
        """

    @property
    def _table_query(self):
        return f"SELECT {self._select()} FROM {self._from()}"
