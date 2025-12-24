# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..constants.fiscal import (
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY,
    FINAL_CUSTOMER,
    FISCAL_COMMENT_DOCUMENT,
    NFE_IND_PRES,
    NFE_IND_PRES_DEFAULT,
)


class FiscalDocumentMixin(models.AbstractModel):
    """
    Provides a collection of reusable methods for Brazilian fiscal document logic.

    This abstract model is intended to be inherited by other models or mixins
    that require fiscal document functionalities, such as preparing fiscal data,
    calculating fiscal amounts, managing document series, and handling comments.

    It is inherited by sale.order, purchase.order, account.move and even stock.picking
    in separate modules. Indeed these business documents need to take care of
    some fiscal parameters before creating Fiscal Documents. And of course,
    Fiscal Document themselves inherit from this mixin.

    Key functionalities include:
    - Computation of various fiscal amounts based on document lines.
    - Inverse methods for distributing header-level costs (freight, insurance)
      to lines.
    - Hooks for customizing data retrieval (e.g., lines, fiscal partner).

    Models using this mixin are often expected to also include fields defined
    in `l10n_br_fiscal.document.mixin` for methods like
    `_prepare_br_fiscal_dict` and `_get_amount_fields` to function
    correctly. Line-based calculations typically rely on an overrideable
    `_get_amount_lines` method.
    """

    _name = "l10n_br_fiscal.document.mixin"
    _description = "Document Fiscal Mixin Fields"

    def _date_server_format(self):
        return fields.Datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _operation_domain(self):
        domain = (
            "[('state', '=', 'approved'),"
            "'|',"
            f"('company_id', '=', {self.env.company.id}),"
            "('company_id', '=', False),"
        )
        return domain

    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop("id", None)

        if default:  # in case you want to use new rather than write later
            return {f"default_{k}": vals[k] for k in vals.keys()}
        return vals

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        if self.document_type_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )

    @api.depends("fiscal_operation_id")
    def _compute_document_type_id(self):
        for doc in self.filtered(lambda doc: doc.fiscal_operation_id):
            if doc.issuer == DOCUMENT_ISSUER_COMPANY and not doc.document_type_id:
                doc.document_type_id = doc.company_id.document_type_id

    def _get_amount_lines(self):
        """Get object lines instances used to compute fiscal fields"""
        return self.mapped(self._get_fiscal_lines_field_name())

    def _get_product_amount_lines(self):
        fiscal_line_ids = self._get_amount_lines()
        return fiscal_line_ids.filtered(lambda line: line.product_id.type != "service")

    @api.model
    def _get_amount_fields(self):
        """Get all fields with 'amount_' prefix"""
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()
        prefixes = ("amount_", "fiscal_amount_")
        amount_fields = [f for f in fields if f.startswith(prefixes)]
        return amount_fields

    @api.depends("document_serie_id", "issuer")
    def _compute_document_serie(self):
        for doc in self:
            if doc.document_serie_id and doc.issuer == DOCUMENT_ISSUER_COMPANY:
                doc.document_serie = doc.document_serie_id.code
            elif doc.document_serie is None:
                doc.document_serie = False

    @api.depends("document_type_id", "issuer")
    def _compute_document_serie_id(self):
        for doc in self:
            if (
                not doc.document_serie_id
                and doc.document_type_id
                and doc.issuer == DOCUMENT_ISSUER_COMPANY
            ):
                doc.document_serie_id = doc.document_type_id.get_document_serie(
                    doc.company_id, doc.fiscal_operation_id
                )
            elif doc.document_serie_id is None:
                doc.document_serie_id = False

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "fiscal_line_ids"

    def _get_fiscal_amount_field_dependencies(self):
        """
        Dynamically get the list of field dependencies.
        """
        if self._abstract:
            return []
        o2m_field_name = self._get_fiscal_lines_field_name()
        target_fields = []
        for field in self._get_amount_fields():
            if (
                field.replace("amount_", "")
                in getattr(self, o2m_field_name)._fields.keys()
            ):
                target_fields.append(field.replace("amount_", ""))

        return [o2m_field_name] + [
            f"{o2m_field_name}.{target_field}" for target_field in target_fields
        ]

    @api.depends(lambda self: self._get_fiscal_amount_field_dependencies())
    def _compute_fiscal_amount(self):
        """
        Compute and sum various fiscal amounts from the document lines.

        This method iterates over fields prefixed with 'amount_' (as determined
        by `_get_amount_fields`) and sums corresponding values from the lines
        retrieved by `_get_amount_lines`.

        It handles cases where delivery costs (freight, insurance, other) are
        defined at the document total level rather than per line.
        """

        fields = self._get_amount_fields()
        for doc in self.filtered(lambda m: m.fiscal_operation_id):
            values = {key: 0.0 for key in fields}
            for line in doc._get_amount_lines():
                for field in fields:
                    if field in line._fields.keys():
                        values[field] += line[field]
                    if field.replace("amount_", "") in line._fields.keys():
                        # FIXME this field creates an error in invoice form
                        if field == "amount_financial_discount_value":
                            values["amount_financial_discount_value"] += (
                                0  # line.financial_discount_value
                            )
                        else:
                            values[field] += line[field.replace("amount_", "")]

            # Valores definidos pelo Total e não pela Linha
            if (
                doc.company_id.delivery_costs == "total"
                or doc.force_compute_delivery_costs_by_total
            ):
                values["amount_freight_value"] = doc.amount_freight_value
                values["amount_insurance_value"] = doc.amount_insurance_value
                values["amount_other_value"] = doc.amount_other_value

            doc.update(values)

    def _get_fiscal_partner(self):
        """
        Hook method to determine the fiscal partner for the document.

        This method is designed to be overridden in implementing models if the
        partner relevant for fiscal purposes (e.g., for tax calculations,
        final consumer status) is different from the main `partner_id`
        of the document record. For instance, an invoice might use a specific
        invoicing contact derived from the main partner.

        :return: A `res.partner` recordset representing the fiscal partner.
        """

        self.ensure_one()
        return self.partner_id

    @api.depends("partner_id")
    def _compute_ind_final(self):
        for doc in self:
            partner = doc._get_fiscal_partner()
            if partner:
                doc.ind_final = partner.ind_final
            else:
                # Default Value
                doc.ind_final = "1"  # Yes

    @api.onchange("ind_final")
    def _inverse_ind_final(self):
        for doc in self:
            for line in doc._get_amount_lines():
                if line.ind_final != doc.ind_final:
                    line.ind_final = doc.ind_final

    @api.depends("fiscal_operation_id")
    def _compute_operation_name(self):
        for doc in self:
            if doc.fiscal_operation_id:
                doc.operation_name = doc.fiscal_operation_id.name
            else:
                doc.operation_name = False

    @api.depends("fiscal_operation_id")
    def _compute_comment_ids(self):
        for doc in self:
            if doc.fiscal_operation_id:
                doc.comment_ids = doc.fiscal_operation_id.comment_ids
            elif doc.comment_ids is None:
                doc.comment_ids = []

    def _distribute_amount_to_lines(self, amount_field_name, line_field_name):
        for record in self:
            if not (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                continue
            lines = record._get_product_amount_lines()
            if not lines:
                continue
            amount_to_distribute = record[amount_field_name]
            total_gross = sum(lines.mapped("price_gross"))
            if total_gross > 0:
                distributed_amount = 0
                for line in lines[:-1]:
                    proportional_amount = record.currency_id.round(
                        amount_to_distribute * (line.price_gross / total_gross)
                    )
                    line[line_field_name] = proportional_amount
                    distributed_amount += proportional_amount
                lines[-1][line_field_name] = amount_to_distribute - distributed_amount
            else:
                lines.write({line_field_name: 0.0})
                if lines:
                    lines[0][line_field_name] = amount_to_distribute

    def _inverse_amount_freight(self):
        self._distribute_amount_to_lines("amount_freight_value", "freight_value")

    def _inverse_amount_insurance(self):
        self._distribute_amount_to_lines("amount_insurance_value", "insurance_value")

    def _inverse_amount_other(self):
        self._distribute_amount_to_lines("amount_other_value", "other_value")

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        domain=lambda self: self._operation_domain(),
    )

    operation_name = fields.Char(
        copy=False,
        compute="_compute_operation_name",
    )

    #
    # Company and Partner are defined here to avoid warnings on runbot
    #
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        index=True,
    )

    fiscal_operation_type = fields.Selection(
        related="fiscal_operation_id.fiscal_operation_type",
    )

    ind_pres = fields.Selection(
        selection=NFE_IND_PRES,
        string="Buyer Presence",
        default=NFE_IND_PRES_DEFAULT,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        string="Comments",
        domain=[("object", "=", FISCAL_COMMENT_DOCUMENT)],
        compute="_compute_comment_ids",
        store=True,
    )

    manual_fiscal_additional_data = fields.Text(
        help="Fiscal Additional data manually entered by user",
    )

    manual_customer_additional_data = fields.Text(
        help="Customer Additional data manually entered by user",
    )

    ind_final = fields.Selection(
        selection=FINAL_CUSTOMER,
        string="Final Consumption Operation",
        compute="_compute_ind_final",
        inverse="_inverse_ind_final",
        store=True,
        precompute=True,
        readonly=False,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
    )

    amount_price_gross = fields.Monetary(
        compute="_compute_fiscal_amount",
        store=True,
        string="Amount Gross",
        help="Amount without discount.",
    )

    fiscal_amount_untaxed = fields.Monetary(
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ibs_base = fields.Monetary(
        string="IBS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ibs_value = fields.Monetary(
        string="IBS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cbs_base = fields.Monetary(
        string="CBS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cbs_value = fields.Monetary(
        string="CBS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icms_base = fields.Monetary(
        string="ICMS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icms_value = fields.Monetary(
        string="ICMS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmsst_base = fields.Monetary(
        string="ICMS ST Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmsst_value = fields.Monetary(
        string="ICMS ST Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmssn_credit_value = fields.Monetary(
        string="ICMSSN Credit Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmsfcp_base = fields.Monetary(
        string="ICMS FCP Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmsfcp_value = fields.Monetary(
        string="ICMS FCP Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icmsfcpst_value = fields.Monetary(
        string="ICMS FCP ST Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icms_destination_value = fields.Monetary(
        string="ICMS Destination Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_icms_origin_value = fields.Monetary(
        string="ICMS Origin Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ipi_base = fields.Monetary(
        string="IPI Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ipi_value = fields.Monetary(
        string="IPI Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ii_base = fields.Monetary(
        string="II Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ii_value = fields.Monetary(
        string="II Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_ii_customhouse_charges = fields.Monetary(
        string="Customhouse Charges",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pis_base = fields.Monetary(
        string="PIS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pis_value = fields.Monetary(
        string="PIS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pisst_base = fields.Monetary(
        string="PIS ST Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pisst_value = fields.Monetary(
        string="PIS ST Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pis_wh_base = fields.Monetary(
        string="PIS Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_pis_wh_value = fields.Monetary(
        string="PIS Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofins_base = fields.Monetary(
        string="COFINS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofins_value = fields.Monetary(
        string="COFINS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofinsst_base = fields.Monetary(
        string="COFINS ST Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofinsst_value = fields.Monetary(
        string="COFINS ST Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofins_wh_base = fields.Monetary(
        string="COFINS Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_cofins_wh_value = fields.Monetary(
        string="COFINS Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_issqn_base = fields.Monetary(
        string="ISSQN Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_issqn_value = fields.Monetary(
        string="ISSQN Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_issqn_wh_base = fields.Monetary(
        string="ISSQN Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_issqn_wh_value = fields.Monetary(
        string="ISSQN Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_csll_base = fields.Monetary(
        string="CSLL Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_csll_value = fields.Monetary(
        string="CSLL Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_csll_wh_base = fields.Monetary(
        string="CSLL Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_csll_wh_value = fields.Monetary(
        string="CSLL Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_irpj_base = fields.Monetary(
        string="IRPJ Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_irpj_value = fields.Monetary(
        string="IRPJ Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_irpj_wh_base = fields.Monetary(
        string="IRPJ Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_irpj_wh_value = fields.Monetary(
        string="IRPJ Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_inss_base = fields.Monetary(
        string="INSS Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_inss_value = fields.Monetary(
        string="INSS Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_inss_wh_base = fields.Monetary(
        string="INSS Ret Base",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_inss_wh_value = fields.Monetary(
        string="INSS Ret Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_estimate_tax = fields.Monetary(
        compute="_compute_fiscal_amount",
        store=True,
    )

    fiscal_amount_tax = fields.Monetary(
        compute="_compute_fiscal_amount",
        store=True,
    )

    fiscal_amount_total = fields.Monetary(
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_tax_withholding = fields.Monetary(
        string="Tax Withholding",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_financial_total = fields.Monetary(
        string="Amount Financial",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_discount_value = fields.Monetary(
        string="Amount Discount",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_financial_total_gross = fields.Monetary(
        string="Amount Financial Gross",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_financial_discount_value = fields.Monetary(
        string="Financial Discount Value",
        compute="_compute_fiscal_amount",
        store=True,
    )

    amount_insurance_value = fields.Monetary(
        string="Insurance Value",
        compute="_compute_fiscal_amount",
        store=True,
        inverse="_inverse_amount_insurance",
    )

    amount_other_value = fields.Monetary(
        string="Other Costs",
        compute="_compute_fiscal_amount",
        store=True,
        inverse="_inverse_amount_other",
    )

    amount_freight_value = fields.Monetary(
        string="Freight Value",
        compute="_compute_fiscal_amount",
        store=True,
        inverse="_inverse_amount_freight",
    )

    # Usado para tornar Somente Leitura os campos totais dos custos
    # de entrega quando a definição for por Linha
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    force_compute_delivery_costs_by_total = fields.Boolean(default=False)

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        compute="_compute_document_type_id",
        store=True,
        precompute=True,
        readonly=False,
    )

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        domain="[('active', '=', True)," "('document_type_id', '=', document_type_id)]",
        compute="_compute_document_serie_id",
        store=True,
    )

    document_serie = fields.Char(
        string="Serie Number",
        compute="_compute_document_serie",
        store=True,
    )

    document_number = fields.Char(
        copy=False,
        index=True,
        unaccent=False,
    )

    document_key = fields.Char(
        string="Key",
        copy=False,
        index=True,
        unaccent=False,
    )

    key_random_code = fields.Char(string="Document Key Random Code")
    key_check_digit = fields.Char(string="Document Key Check Digit")
    total_weight = fields.Float()
