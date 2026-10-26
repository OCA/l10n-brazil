# Copyright (C) 2015  Luis Felipe Miléo - KMEE <mileo@kmee.com.br>
# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ibpt_api = fields.Boolean(
        string="Use IBPT API",
        related="company_id.ibpt_api",
        readonly=False,
    )

    ibpt_token = fields.Char(
        string="IBPT Token",
        related="company_id.ibpt_token",
        readonly=False,
    )

    ibpt_update_days = fields.Integer(
        string="IBPT Update",
        related="company_id.ibpt_update_days",
        readonly=False,
    )

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        related="company_id.document_type_id",
        string="Default Document Type",
    )

    module_l10n_br_nfe = fields.Boolean(
        string="NF-e/NFC-e",
    )

    module_l10n_br_mdfe = fields.Boolean(
        string="MDF-e",
    )

    module_l10n_br_nfse = fields.Boolean(
        string="NFS-e",
    )

    module_l10n_br_cte = fields.Boolean(
        string="CT-e",
    )

    delivery_costs = fields.Selection(
        related="company_id.delivery_costs", readonly=False
    )

    report_company_fiscal_data = fields.Boolean(
        related="company_id.report_company_fiscal_data", readonly=False
    )

    report_tax_framework = fields.Boolean(
        related="company_id.report_tax_framework", readonly=False
    )

    report_partner_fiscal_data = fields.Boolean(
        related="company_id.report_partner_fiscal_data", readonly=False
    )

    report_fiscal_operation = fields.Boolean(
        related="company_id.report_fiscal_operation", readonly=False
    )

    report_line_classification = fields.Boolean(
        related="company_id.report_line_classification", readonly=False
    )

    report_line_cfop = fields.Boolean(
        related="company_id.report_line_cfop", readonly=False
    )

    report_line_operation_line = fields.Boolean(
        related="company_id.report_line_operation_line", readonly=False
    )

    report_fiscal_totals = fields.Boolean(
        related="company_id.report_fiscal_totals", readonly=False
    )

    report_withholding_display = fields.Selection(
        related="company_id.report_withholding_display", readonly=False
    )

    report_included_taxes = fields.Boolean(
        related="company_id.report_included_taxes", readonly=False
    )
