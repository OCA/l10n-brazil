# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from erpbrasil.base import fiscal


class DocumentRelated(models.Model):
    _name = 'l10n_br_fiscal.document.related'
    _description = 'Fiscal Document Related'

    fiscal_document_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document',
        index=True)

    document_related_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document',
        string='Fiscal Document Related',
        index=True)

    document_type_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.document.type',
        string='Fiscal Document Type')

    document_type_code = fields.Char(
        related='document_type_id.code')

    document_key = fields.Char(
        string='Document Key',
        size=44)

    serie = fields.Char(
        string='Serie',
        size=12)

    number = fields.Char(
        string='Number',
        size=32)

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain=[('country_id.code', '=', 'BR')])

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18)

    cpfcnpj_type = fields.Selection(
        selection=[
            ('cpf', 'CPF'),
            ('cnpj', 'CNPJ')],
        string='Type Doc Number',
        default='cnpj')

    inscr_est = fields.Char(
        string='Inscr. Estadual/RG',
        size=16)

    date = fields.Date(
        string='Data')

    @api.multi
    @api.constrains('cnpj_cpf')
    def _check_cnpj_cpf(self):
        result = True
        for record in self:
            if record.cnpj_cpf:
                disable_cnpj_ie_validation = record.env[
                    'ir.config_parameter'].sudo().get_param(
                        'l10n_br_base.disable_cpf_cnpj_validation',
                        default=False)

                if not disable_cnpj_ie_validation:
                    if record.cpfcnpj_type == 'cnpj':
                        if not fiscal.cnpj_cpf.validar(record.cnpj_cpf):
                            result = False
                            document = "CNPJ"
                    elif record.cpfcnpj_type == 'cpf':
                        result = False
                        document = "CPF"

                    if not result:
                        raise ValidationError(
                            _("{} Invalid!").format(document)
                        )

    @api.multi
    @api.constrains('inscr_est', 'state_id')
    def _check_ie(self):
        for record in self:
            result = True

            disable_ie_validation = record.env[
                'ir.config_parameter'].sudo().get_param(
                    'l10n_br_base.disable_ie_validation', default=False)

            if not disable_ie_validation:
                if record.inscr_est and record.state_id:
                    state_code = record.state_id.code or ""
                    uf = state_code.lower()
                    result = fiscal.ie.validar(uf, record.inscr_est)
                if not result:
                    raise ValidationError(_("Estadual Inscription Invalid !"))

    @api.onchange('document_related_id')
    def _onchange_document_related_id(self):
        related = self.document_related_id
        if not related:
            return False

        self.document_type_id = related.document_type_id

        if related.document_type_id.electronic:
            self.document_key = related.key
            self.serie = False
            self.number = False
            self.state_id = False
            self.cnpj_cpf = False
            self.cpfcnpj_type = False
            self.date = False
            self.inscr_est = False

        if related.document_type_id.code in ('01', '04'):
            self.access_key = False
            self.serie = related.document_serie
            self.number = related.number
            self.state_id = related.partner_id and \
                related.partner_id.state_id and \
                related.partner_id.state_id.id or False

            self.cnpj_cpf = related.partner_id and \
                related.partner_id.cnpj_cpf or False

            if related.partner_id.is_company:
                self.cpfcnpj_type = 'cnpj'
            else:
                self.cpfcnpj_type = 'cpf'

            self.date = related.date

        if related.document_type_id.code == '04':
            self.inscr_est = related.partner_id and \
                related.partner_id.inscr_est or False

    @api.onchange('cnpj_cpf', 'cpfcnpj_type')
    def _onchange_mask_cnpj_cpf(self):
        self.cnpj_cpf = fiscal.cnpj_cpf.formata(str(self.cnpj_cpf))
