# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    FISCAL_COMMENT_LINE,
    NFE_IND_IE_DEST,
    OPERATION_STATE,
    OPERATION_STATE_DEFAULT,
    PRODUCT_FISCAL_TYPE,
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_IPI,
    TAX_DOMAIN_ISSQN,
    TAX_FRAMEWORK,
    TAX_FRAMEWORK_NORMAL,
    TAX_ICMS_OR_ISSQN,
)
from ..constants.icms import ICMS_ORIGIN


class OperationLine(models.Model):
    _name = "l10n_br_fiscal.operation.line"
    _description = "Fiscal Operation Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        ondelete="cascade",
        required=True,
    )

    name = fields.Char(required=True)

    document_type_id = fields.Many2one(comodel_name="l10n_br_fiscal.document.type")

    cfop_internal_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP Internal",
        domain="[('type_in_out', '=', fiscal_operation_type), "
        "('destination', '=', '1'),"
        "('type_move', '=ilike', fiscal_type + '%')]",
    )

    cfop_external_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP External",
        domain="[('type_in_out', '=', fiscal_operation_type), "
        "('type_move', '=ilike', fiscal_type + '%'), "
        "('destination', '=', '2')]",
    )

    cfop_export_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP Export",
        domain="[('type_in_out', '=', fiscal_operation_type), "
        "('type_move', '=ilike', fiscal_type + '%'), "
        "('destination', '=', '3')]",
    )

    fiscal_operation_type = fields.Selection(
        related="fiscal_operation_id.fiscal_operation_type",
        string="Fiscal Operation Type",
        store=True,
    )

    fiscal_type = fields.Selection(
        related="fiscal_operation_id.fiscal_type",
        string="Fiscal Type",
        store=True,
    )

    tax_icms_or_issqn = fields.Selection(
        selection=TAX_ICMS_OR_ISSQN,
        string="ICMS or ISSQN Tax",
    )

    line_inverse_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line Inverse",
        domain="[('fiscal_operation_type', '!=', fiscal_operation_type)]",
        copy=False,
    )

    line_refund_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line Refund",
        domain="[('fiscal_operation_type', '!=', fiscal_operation_type)]",
        copy=False,
    )

    partner_tax_framework = fields.Selection(selection=TAX_FRAMEWORK)

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string="ICMS Taxpayer",
    )

    product_type = fields.Selection(
        selection=PRODUCT_FISCAL_TYPE, string="Product Fiscal Type"
    )

    company_tax_framework = fields.Selection(selection=TAX_FRAMEWORK)

    add_to_amount = fields.Boolean(string="Add to Document Amount?", default=True)

    icms_origin = fields.Selection(selection=ICMS_ORIGIN, string="Origin")

    tax_definition_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.tax.definition",
        inverse_name="fiscal_operation_line_id",
        string="Tax Definition",
        copy=True,
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        domain=[("object", "=", FISCAL_COMMENT_LINE)],
        string="Comment",
    )

    state = fields.Selection(
        selection=OPERATION_STATE,
        default=OPERATION_STATE_DEFAULT,
        index=True,
        readonly=True,
        tracking=True,
        copy=False,
    )

    date_start = fields.Datetime(string="Start Date")

    date_end = fields.Datetime(string="End Date")

    _sql_constraints = [
        (
            "fiscal_operation_name_uniq",
            "unique (name, fiscal_operation_id)",
            _("Fiscal Operation Line already exists with this name !"),
        )
    ]

    def get_document_type(self, company):
        self.ensure_one()
        if self.document_type_id:
            document_type = self.document_type_id
        else:
            if not company.document_type_id:
                raise UserError(
                    _("You need to set a default fiscal document in your company!")
                )

            document_type = company.document_type_id

        return document_type

    def _get_cfop(self, company, partner):
        cfop = self.env["l10n_br_fiscal.cfop"]
        if partner.state_id == company.state_id:
            cfop = self.cfop_internal_id
        if partner.state_id != company.state_id:
            cfop = self.cfop_external_id
        if partner.country_id != company.country_id:
            cfop = self.cfop_export_id
        return cfop

    def _build_mapping_result_ipi(self, mapping_result, tax_definition):
        if tax_definition and tax_definition.ipi_guideline_id:
            mapping_result["ipi_guideline"] = tax_definition.ipi_guideline_id

    def _build_mapping_result_icms(self, mapping_result, tax_definition):
        if tax_definition and tax_definition.is_benefit:
            mapping_result["icms_tax_benefit_id"] = tax_definition.id

    def _build_mapping_result(self, mapping_result, tax_definition):
        mapping_result["taxes"][tax_definition.tax_domain] = tax_definition.tax_id
        self._build_mapping_result_icms(
            mapping_result,
            tax_definition.filtered(lambda t: t.tax_domain == TAX_DOMAIN_ICMS),
        )
        self._build_mapping_result_ipi(
            mapping_result,
            tax_definition.filtered(lambda t: t.tax_domain == TAX_DOMAIN_IPI),
        )

    def map_fiscal_taxes(
        self,
        company,
        partner,
        product=None,
        fiscal_price=None,
        fiscal_quantity=None,
        ncm=None,
        nbm=None,
        nbs=None,
        cest=None,
        city_taxation_code=None,
        service_type=None,
        ind_final=None,
    ):
        """
        Map and determine the applicable fiscal taxes, CFOP, IPI guideline,
        and ICMS tax benefit for a given context.

        The method aggregates tax definitions from various sources, applying a
        precedence order:
        1. Company-level tax definitions.
        2. NCM-defined taxes (IPI, II).
        3. ICMS Regulation specific taxes.
        4. Taxes defined directly on this fiscal operation line.
        5. Taxes defined on the determined CFOP.
        6. Taxes from the partner's fiscal profile.

        It also filters taxes based on whether the product is subject to
        ICMS or ISSQN.

        :param company: The company record (res.company).
        :param partner: The partner record (res.partner).
        :param product: Optional product record (product.product).
        :param fiscal_price: (Unused in direct logic; kept for signature
            consistency for overrides/extensions)
        :param fiscal_quantity: (Unused in direct logic; kept for signature
            consistency for overrides/extensions)
        :param ncm: Optional NCM record (l10n_br_fiscal.ncm);
            defaults to product's NCM.
        :param nbm: Optional NBM record (l10n_br_fiscal.nbm);
            defaults to product's NBM.
        :param nbs: Optional NBS record (l10n_br_fiscal.nbs);
            defaults to product's NBS.
        :param cest: Optional CEST record (l10n_br_fiscal.cest);
            defaults to product's CEST.
        :param city_taxation_code: Optional City Taxation Code record
            (l10n_br_fiscal.city.taxation.code).
        :param service_type: Optional Service Type record
            (l10n_br_fiscal.service.type).
        :param ind_final: (Passed to icms_regulation_id.map_tax; not directly
            used for tax calculation here)
        :return: A dictionary containing:
            - 'taxes': A dictionary of applicable tax records
              (l10n_br_fiscal.tax) keyed by their tax_domain.
            - 'cfop': The determined CFOP record (l10n_br_fiscal.cfop).
            - 'ipi_guideline': The determined IPI guideline record
              (l10n_br_fiscal.tax.ipi.guideline).
            - 'icms_tax_benefit_id': The determined ICMS tax benefit record
              ID (l10n_br_fiscal.tax.definition) or False.
        """
        mapping_result = {
            "taxes": {},
            "cfop": False,
            "ipi_guideline": self.env.ref("l10n_br_fiscal.tax_guideline_999"),
            "icms_tax_benefit_id": False,
        }

        self.ensure_one()

        # Define CFOP
        mapping_result["cfop"] = self._get_cfop(company, partner)

        # 1 Get Tax Defs from Company
        for tax_definition in company.tax_definition_ids.map_tax_definition(
            company,
            partner,
            product,
            ncm=ncm,
            nbm=nbm,
            nbs=nbs,
            cest=cest,
            city_taxation_code=city_taxation_code,
            service_type=service_type,
        ):
            self._build_mapping_result(mapping_result, tax_definition)

        # 2 From NCM
        if not ncm and product:
            ncm = product.ncm_id

        if company.tax_framework == TAX_FRAMEWORK_NORMAL:
            tax_ipi = ncm.tax_ipi_id
            tax_ii = ncm.tax_ii_id
            mapping_result["taxes"][tax_ipi.tax_domain] = tax_ipi

            if mapping_result["cfop"].destination == CFOP_DESTINATION_EXPORT:
                mapping_result["taxes"][tax_ii.tax_domain] = tax_ii

            # 3 From ICMS Regulation
            if company.icms_regulation_id:
                icms_taxes, icms_tax_defs = company.icms_regulation_id.map_tax(
                    company=company,
                    partner=partner,
                    product=product,
                    ncm=ncm,
                    nbm=nbm,
                    cest=cest,
                    operation_line=self,
                    ind_final=ind_final,
                )

                for tax_def in icms_tax_defs:
                    self._build_mapping_result_icms(mapping_result, tax_def)

                for tax in icms_taxes:
                    mapping_result["taxes"][tax.tax_domain] = tax

        # 4 From Operation Line
        for tax_definition in self.tax_definition_ids.map_tax_definition(
            company,
            partner,
            product,
            ncm=ncm,
            nbm=nbm,
            nbs=nbs,
            cest=cest,
            city_taxation_code=city_taxation_code,
            service_type=service_type,
        ):
            self._build_mapping_result(mapping_result, tax_definition)

        # 5 From CFOP
        for tax_definition in mapping_result[
            "cfop"
        ].tax_definition_ids.map_tax_definition(
            company,
            partner,
            product,
            ncm=ncm,
            nbm=nbm,
            nbs=nbs,
            cest=cest,
            city_taxation_code=city_taxation_code,
            service_type=service_type,
        ):
            self._build_mapping_result(mapping_result, tax_definition)

        # 6 From Partner Profile
        for (
            tax_definition
        ) in partner.fiscal_profile_id.tax_definition_ids.map_tax_definition(
            company,
            partner,
            product,
            ncm=ncm,
            nbm=nbm,
            nbs=nbs,
            cest=cest,
            city_taxation_code=city_taxation_code,
            service_type=service_type,
        ):
            self._build_mapping_result(mapping_result, tax_definition)

        if product.tax_icms_or_issqn == TAX_DOMAIN_ICMS:
            mapping_result["taxes"].pop(TAX_DOMAIN_ISSQN, None)
        elif product.tax_icms_or_issqn == TAX_DOMAIN_ISSQN:
            mapping_result["taxes"].pop(TAX_DOMAIN_ICMS, None)
        else:
            mapping_result["taxes"].pop(TAX_DOMAIN_ICMS, None)
            mapping_result["taxes"].pop(TAX_DOMAIN_ISSQN, None)

        return mapping_result

    def action_review(self):
        self.write({"state": "review"})

    def unlink(self):
        lines = self.filtered(lambda line: line.state == "approved")
        if lines:
            raise UserError(
                _("You cannot delete an Operation Line which is not draft !")
            )
        return super().unlink()

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        if not self.fiscal_operation_id.fiscal_operation_type:
            warning = {
                "title": _("Warning!"),
                "message": _("You must first select a operation type."),
            }
            return {"warning": warning}
