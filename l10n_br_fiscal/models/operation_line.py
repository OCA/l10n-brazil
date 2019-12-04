# Copyright (C) 2019  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants.fiscal import (FISCAL_IN_OUT_ALL, NFE_IND_IE_DEST,
                                NFE_IND_IE_DEST_DEFAULT, OPERATION_STATE,
                                OPERATION_STATE_DEFAULT, PRODUCT_FISCAL_TYPE,
                                TAX_FRAMEWORK)
from ..constants.icms import ICMS_ORIGIN


class OperationLine(models.Model):
    _name = "l10n_br_fiscal.operation.line"
    _description = "Fiscal Operation Line"
    _inherit = ["mail.thread"]

    operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Operation",
        ondelete="cascade",
        required=True,
    )

    name = fields.Char(string="Name", required=True)

    cfop_internal_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP Internal",
        domain="[('type_in_out', '=', operation_type)," "('destination', '=', '1')]",
    )

    cfop_external_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP External",
        domain="[('type_in_out', '=', operation_type)," "('destination', '=', '2')]",
    )

    cfop_export_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cfop",
        string="CFOP Export",
        domain="[('type_in_out', '=', operation_type)," "('destination', '=', '3')]",
    )

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT_ALL,
        related="operation_id.operation_type",
        string="Operation Type",
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env["res.company"]._company_default_get(
            "l10n_br_fiscal.operation.line"
        ),
    )

    line_inverse_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line Inverse",
        domain="[('operation_type', '!=', operation_type)]",
        copy=False,
    )

    line_refund_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line Refund",
        domain="[('operation_type', '!=', operation_type)]",
        copy=False,
    )

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK, string="Partner Tax Framework"
    )

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string="Contribuinte do ICMS",
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT,
    )

    product_type = fields.Selection(selection=PRODUCT_FISCAL_TYPE, string="Fiscal Type")

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK, string="Copmpany Tax Framework"
    )

    add_to_amount = fields.Boolean(string="Add to Document Amount?", default=True)

    # ICMS Fields
    icms_custom = fields.Boolean(string="Custom ICMS", default=False)

    icms_origin = fields.Selection(selection=ICMS_ORIGIN, string="Origin", default="0")

    icms_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax ICMS",
        domain="[('tax_domain', '=', 'icms')]",
    )

    icms_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST ICMS",
        domain="[('cst_type', '=', 'all')," "('tax_domain', '=', 'icms')]",
    )

    """
    motivo_icms_desonerado = fields.Selection(
        selection=MOTIVO_DESONERACAO_ICMS,
        string='Motivo da desoneração do ICMS')
    """

    icms_cst_csosn_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CSOSN",
        domain="[('cst_type', '=', 'all')," "('tax_domain', '=', 'simples')]",
    )

    icms_base_add_ipi = fields.Boolean(string="Add IPI value in ICMS base amount?")

    icms_st_base_add_ipi = fields.Boolean(
        string="Add IPI value in ICMS ST base amount?"
    )

    # IPI Fields
    ipi_custom = fields.Boolean(string="Custom IPI", default=False)

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

    ipi_guideline_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.ipi.guideline", string="IPI Guideline"
    )

    # PIS/COFINS Fields
    pis_cofins_custom = fields.Boolean(string="Custom PIS/COFINS", default=False)

    # PIS Fields
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

    # Cofins Fields
    cofins_tax_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax",
        string="Tax Cofins",
        domain="[('tax_domain', '=', 'cofins')]",
    )

    cofins_cst_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cst",
        string="CST COFINS",
        domain="[('cst_type', '=', operation_type)," "('tax_domain', '=', 'cofins')]",
    )

    pis_cofins_revenue_code = fields.Char(string="PIS/COFINS Revenue Code", size=3)

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="l10n_br_fiscal_operation_line_comment_rel",
        column1="operation_id",
        column2="comment_id",
        string="Comment",
    )

    state = fields.Selection(
        selection=OPERATION_STATE,
        string="State",
        default=OPERATION_STATE_DEFAULT,
        index=True,
        readonly=True,
        track_visibility="onchange",
        copy=False,
    )

    _sql_constraints = [
        (
            "fiscal_operation_name_uniq",
            "unique (name, operation_id)",
            _("Fiscal Operation Line already exists with this name !"),
        )
    ]

    @api.multi
    def action_review(self):
        self.write({"state": "review"})

    @api.multi
    def unlink(self):
        lines = self.filtered(lambda l: l.state == "approved")
        if lines:
            raise UserError(
                _("You cannot delete an Operation Line which is not draft !")
            )
        return super(OperationLine, self).unlink()

    @api.multi
    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        if not self.operation_id.operation_type:
            warning = {
                "title": _("Warning!"),
                "message": _("You must first select a operation type."),
            }
            return {"warning": warning}
