# Copyright (C) 2021  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

from ..constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    NFE_IND_IE_DEST,
    TAX_FRAMEWORK,
)


class FiscalDocumentInvoiceMixin(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.invoice.mixin'
    _description = 'Invoice Document Fiscal Mixin'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )

    partner_legal_name = fields.Char(
        string='Legal Name',
        related='partner_id.legal_name',
    )

    partner_name = fields.Char(
        string='Name',
        related='partner_id.name',
    )

    partner_cnpj_cpf = fields.Char(
        string='CNPJ',
        related='partner_id.cnpj_cpf',
    )

    partner_inscr_est = fields.Char(
        string='State Tax Number',
        related='partner_id.inscr_est',
    )

    partner_ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string='Contribuinte do ICMS',
        related='partner_id.ind_ie_dest',
    )

    partner_inscr_mun = fields.Char(
        string='Municipal Tax Number',
        related='partner_id.inscr_mun',
    )

    partner_suframa = fields.Char(
        string='Suframa',
        related='partner_id.suframa',
    )

    partner_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Main CNAE',
        related='partner_id.cnae_main_id',
    )

    partner_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Tax Framework',
        related='partner_id.tax_framework',
    )

    partner_street = fields.Char(
        string='Partner Street',
        related='partner_id.street',
    )

    partner_number = fields.Char(
        string='Partner Number',
        related='partner_id.street_number',
    )

    partner_street2 = fields.Char(
        string='Partner Street2',
        related='partner_id.street2',
    )

    partner_district = fields.Char(
        string='Partner District',
        related='partner_id.district',
    )

    partner_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Partner Country',
        related='partner_id.country_id',
    )

    partner_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Partner State',
        related='partner_id.state_id',
    )

    partner_city_id = fields.Many2one(
        comodel_name='res.city',
        string='Partner City',
        related='partner_id.city_id',
    )

    partner_zip = fields.Char(
        string='Partner Zip',
        related='partner_id.zip',
    )

    partner_phone = fields.Char(
        string='Partner Phone',
        related='partner_id.phone',
    )

    partner_is_company = fields.Boolean(
        string='Partner Is Company?',
        related='partner_id.is_company',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
    )

    processador_edoc = fields.Selection(
        related='company_id.processador_edoc',
    )

    company_legal_name = fields.Char(
        string='Company Legal Name',
        related='company_id.legal_name',
    )

    company_name = fields.Char(
        string='Company Name',
        size=128,
        related='company_id.name',
    )

    company_cnpj_cpf = fields.Char(
        string='Company CNPJ',
        related='company_id.cnpj_cpf',
    )

    company_inscr_est = fields.Char(
        string='Company State Tax Number',
        related='company_id.inscr_est',
    )

    company_inscr_mun = fields.Char(
        string='Company Municipal Tax Number',
        related='company_id.inscr_mun',
    )

    company_suframa = fields.Char(
        string='Company Suframa',
        related='company_id.suframa',
    )

    company_cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.cnae',
        string='Company Main CNAE',
        related='company_id.cnae_main_id',
    )

    company_tax_framework = fields.Selection(
        selection=TAX_FRAMEWORK,
        string='Company Tax Framework',
        related='company_id.tax_framework',
    )

    company_street = fields.Char(
        string='Company Street',
        related='company_id.street',
    )

    company_number = fields.Char(
        string='Company Number',
        related='company_id.street_number',
    )

    company_street2 = fields.Char(
        string='Company Street2',
        related='company_id.street2',
    )

    company_district = fields.Char(
        string='Company District',
        related='company_id.district',
    )

    company_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Company Country',
        related='company_id.country_id',
    )

    company_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Company State',
        related='company_id.state_id',
    )

    company_city_id = fields.Many2one(
        comodel_name='res.city',
        string='Company City',
        related='company_id.city_id',
    )

    company_zip = fields.Char(
        string='Company ZIP',
        related='company_id.zip',
    )

    company_phone = fields.Char(
        string='Company Phone',
        related='company_id.phone',
    )

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        if self.document_type_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id)

    @api.onchange('document_serie_id')
    def _onchange_document_serie_id(self):
        if self.document_serie_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie = self.document_serie_id.code
