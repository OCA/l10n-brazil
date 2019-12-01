# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from ..constants.fiscal import FISCAL_IN_OUT, TAX_FRAMEWORK


class DocumentAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.document.abstract"
    _inherit = ["mail.thread", "mail.activity.mixin", "l10n_br_fiscal.document.mixin"]
    _description = "Fiscal Document Abstract"

    @api.one
    @api.depends("line_ids")
    def _compute_amount(self):
        self.amount_untaxed = sum(line.amount_untaxed for line in self.line_ids)
        self.amount_icms_base = sum(line.icms_base for line in self.line_ids)
        self.amount_icms_value = sum(line.icms_value for line in self.line_ids)
        self.amount_ipi_base = sum(line.ipi_base for line in self.line_ids)
        self.amount_ipi_value = sum(line.ipi_value for line in self.line_ids)
        self.amount_pis_base = sum(line.pis_base for line in self.line_ids)
        self.amount_pis_value = sum(line.pis_value for line in self.line_ids)
        self.amount_cofins_base = sum(line.cofins_base for line in self.line_ids)
        self.amount_cofins_value = sum(line.cofins_value for line in self.line_ids)
        self.amount_tax = sum(line.amount_tax for line in self.line_ids)
        self.amount_discount_value = sum(line.discount_value for line in self.line_ids)
        self.amount_insurance_value = sum(line.insurance_value for line in self.line_ids)
        self.amount_other_costs_value = sum(line.other_costs_value for line in self.line_ids)
        self.amount_freight_value = sum(line.freight_value for line in self.line_ids)
        self.amount_total = sum(line.amount_total for line in self.line_ids)

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string="Active",
        default=True)

    number = fields.Char(
        string="Number",
        index=True)

    key = fields.Char(
        string="key",
        index=True)

    issuer = fields.Selection(
        selection=[("company", "Company"), ("partner", "Partner")],
        default="company",
        required=True,
        string="Issuer")

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        index=True,
        default=lambda self: self.env.user)

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        related='document_serie_id.document_type_id',
        required=True)

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?")

    date = fields.Datetime(
        string="Date")

    date_in_out = fields.Datetime(
        string="Date Move")

    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        domain="[('active', '=', True),"
               "('document_type_id', '=', document_type_id)]")

    document_serie = fields.Char(
        string="Serie Number")

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner")

    partner_legal_name = fields.Char(
        string="Legal Name")

    partner_name = fields.Char(
        string="Name")

    partner_cnpj_cpf = fields.Char(
        string="CNPJ")

    partner_inscr_est = fields.Char(
        string="State Tax Number")

    partner_inscr_mun = fields.Char(
        string="Municipal Tax Number")

    partner_suframa = fields.Char(
        string="Suframa")

    partner_cnae_main_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        string="Main CNAE")

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string="Tax Framework")

    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner",
        string="Shipping Address")

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env["res.company"]._company_default_get(
            "l10n_br_fiscal.document"))

    company_legal_name = fields.Char(
        string="Company Legal Name",
        related="company_id.legal_name")

    company_name = fields.Char(
        string="Company Name",
        related="company_id.name",
        size=128)

    company_cnpj_cpf = fields.Char(
        string="Company CNPJ",
        related="company_id.cnpj_cpf")

    company_inscr_est = fields.Char(
        string="Company State Tax Number",
        related="company_id.inscr_est")

    company_inscr_mun = fields.Char(
        string="Company Municipal Tax Number",
        related="company_id.inscr_mun")

    company_suframa = fields.Char(
        string="Company Suframa",
        related="company_id.suframa")

    company_cnae_main_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.cnae",
        related="company_id.cnae_main_id",
        string="Company Main CNAE")

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        related="company_id.tax_framework",
        string="Company Tax Framework")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        store=True,
        readonly=True)

    amount_untaxed = fields.Monetary(
        string="Amount Untaxed",
        compute="_compute_amount")

    amount_icms_base = fields.Monetary(
        string="ICMS Base",
        compute="_compute_amount")

    amount_icms_value = fields.Monetary(
        string="ICMS Value",
        compute="_compute_amount")

    amount_ipi_base = fields.Monetary(
        string="IPI Base",
        compute="_compute_amount")

    amount_ipi_value = fields.Monetary(
        string="IPI Value",
        compute="_compute_amount")

    amount_pis_base = fields.Monetary(
        string="PIS Base",
        compute="_compute_amount")

    amount_pis_value = fields.Monetary(
        string="PIS Value",
        compute="_compute_amount")

    amount_cofins_base = fields.Monetary(
        string="COFINS Base",
        compute="_compute_amount")

    amount_cofins_value = fields.Monetary(
        string="COFINS Value",
        compute="_compute_amount")

    amount_tax = fields.Monetary(
        string="Amount Tax",
        compute="_compute_amount")

    amount_total = fields.Monetary(
        string="Amount Total",
        compute="_compute_amount")

    amount_discount = fields.Monetary(
        string="Amount Discount",
        compute="_compute_amount")

    amount_insurance_value = fields.Monetary(
        string="Insurance Value",
        default=0.00,
        compute="_compute_amount")

    amount_other_costs_value = fields.Monetary(
        string="Other Costs",
        default=0.00,
        compute="_compute_amount")

    amount_freight_value = fields.Monetary(
        string="Freight Value",
        default=0.00,
        compute="_compute_amount")

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("done", "Done"),
            ("cancelled", "Cancelled")],
        string="State",
        default="draft",
        index=True,
        readonly=True,
        track_visibility="onchange",
        copy=False)

    line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line.abstract",
        inverse_name="document_id",
        string="Document Lines")

    @api.model
    def _create_serie_number(self, document_serie_id, document_date):
        document_serie = self.env['l10n_br_fiscal.document.serie'].browse(
            document_serie_id)
        return document_serie.internal_sequence_id.with_context(
            ir_sequence_date=document_date)._next()

    @api.model
    def create(self, values):
        if not values.get('date'):
            values['date'] = fields.Datetime.now().strftime(
                DEFAULT_SERVER_DATETIME_FORMAT)

        if values.get('document_serie_id') and not values.get('number'):
            values['number'] = self._create_serie_number(
                values.get('document_serie_id'), values['date'])

        return super(DocumentAbstract, self).create(values)

    @api.onchange("document_serie_id")
    def _onchange_document_serie_id(self):
        if self.document_serie_id:
            self.document_serie = self.document_serie_id.code

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_legal_name = self.partner_id.legal_name
            self.partner_name = self.partner_id.name
            self.partner_cnpj_cpf = self.partner_id.cnpj_cpf
            self.partner_inscr_est = self.partner_id.inscr_est
            self.partner_inscr_mun = self.partner_id.inscr_mun
            self.partner_suframa = self.partner_id.suframa
            self.partner_cnae_main_id = self.partner_id.cnae_main_id
            self.partner_tax_framework = self.partner_id.tax_framework

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        self.document_type_id = self.company_id.default_document_type_id

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        serie = self.env['l10n_br_fiscal.document.serie']
        if self.document_type_id:
            serie = self.env['l10n_br_fiscal.document.serie'].search([
                ('company_id', '=', self.company_id.id),
                ('document_type_id', '=', self.document_type_id.id),
                ('active', '=', True)])

        self.document_serie_id = serie

    @api.multi
    def _action_confirm(self):
        for d in self:
            if not d.number:
                number = self._create_serie_number(d.document_serie_id.id)
                d = number

            d.state = 'open'
