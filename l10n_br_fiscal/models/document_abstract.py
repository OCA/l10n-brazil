# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2019  Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import (
    TAX_FRAMEWORK,
    DOCUMENT_ISSUER,
    DOCUMENT_ISSUER_COMPANY
)


class DocumentAbstract(models.AbstractModel):
    _name = "l10n_br_fiscal.document.abstract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fiscal Document Abstract"

    """ Implementação base dos documentos fiscais

    Devemos sempre ter em mente que o modelo que vai usar este módulo abstrato
     tem diversos metodos importantes e a intenção que os módulos da OCA que
     extendem este modelo, funcionem se possível sem a necessidade de
     codificação extra.

    É preciso também estar atento que o documento fiscal tem dois estados:

    - Estado do documento eletrônico / não eletônico: state_edoc
    - Estado FISCAL: state_fiscal

    O estado fiscal é um campo que é alterado apenas algumas vezes pelo código
    e é de responsabilidade do responsável fiscal pela empresa de manter a
    integridade do mesmo, pois ele não tem um fluxo realmente definido e
    interfere no lançamento do registro no arquivo do SPED FISCAL.
    """

    @api.depends("line_ids")
    def _compute_amount(self):
        for record in self:
            record.amount_untaxed = sum(
                line.amount_untaxed for line in record.line_ids)
            record.amount_icms_base = sum(
                line.icms_base for line in record.line_ids)
            record.amount_icms_value = sum(
                line.icms_value for line in record.line_ids)
            record.amount_ipi_base = sum(
                line.ipi_base for line in record.line_ids)
            record.amount_ipi_value = sum(
                line.ipi_value for line in record.line_ids)
            record.amount_pis_base = sum(
                line.pis_base for line in record.line_ids)
            record.amount_pis_value = sum(
                line.pis_value for line in record.line_ids)
            record.amount_cofins_base = sum(
                line.cofins_base for line in record.line_ids)
            record.amount_cofins_value = sum(
                line.cofins_value for line in record.line_ids)
            record.amount_tax = sum(
                line.amount_tax for line in record.line_ids)
            record.amount_discount = sum(
                line.discount_value for line in record.line_ids)
            record.amount_insurance_value = sum(
                line.insurance_value for line in record.line_ids)
            record.amount_other_costs_value = sum(
                line.other_costs_value for line in record.line_ids)
            record.amount_freight_value = sum(
                line.freight_value for line in record.line_ids)
            record.amount_total = sum(
                line.amount_total for line in record.line_ids)

    # used mostly to enable _inherits of account.invoice on fiscal_document
    # when existing invoices have no fiscal document.
    active = fields.Boolean(
        string="Active",
        default=True)

    number = fields.Char(
        string="Number",
        copy=False,
        index=True)

    key = fields.Char(
        string="key",
        copy=False,
        index=True)

    issuer = fields.Selection(
        selection=DOCUMENT_ISSUER,
        default=DOCUMENT_ISSUER_COMPANY,
        required=True,
        string="Issuer")

    date = fields.Datetime(
        string="Date",
        copy=False)

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        index=True,
        default=lambda self: self.env.user)

    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        required=True)

    operation_name = fields.Char(
        string="Operation",
    )

    document_electronic = fields.Boolean(
        related="document_type_id.electronic",
        string="Electronic?",
        store=True)

    date_in_out = fields.Datetime(
        string="Date Move",
        copy=False)

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

    processador_edoc = fields.Selection(
        related="company_id.processador_edoc",
        store=True)

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
            values['date'] = self._date_server_format()

        if values.get('document_serie_id') and not values.get('number'):
            values['number'] = self._create_serie_number(
                values.get('document_serie_id'), values['date'])

        return super(DocumentAbstract, self).create(values)

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

    def _set_document_serie(self):
        if self.operation_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            if self.document_type_id:
                self.document_serie_id = self.operation_id.get_document_serie(
                    self.company_id, self.document_type_id)

                if not self.document_serie_id:
                    self.document_serie_id = self.env[
                        'l10n_br_fiscal.document.serie'].search([
                            ('company_id', '=', self.company_id.id),
                            ('document_type_id', '=', self.document_type_id.id),
                            ('active', '=', True)], limit=1, order="code")

        if not self.operation_id:
            self.document_type_id = self.company_id.default_document_type_id

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        self._set_document_serie()
        if self.operation_id:
            self.operation_name = self.operation_id.name

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        self._set_document_serie()

    @api.onchange("document_serie_id")
    def _onchange_document_serie_id(self):
        if self.document_serie_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie = self.document_serie_id.code
