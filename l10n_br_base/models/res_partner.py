# -*- coding: utf-8 -*-
# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import models, fields, api
from ..tools import fiscal
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _display_address(self, without_company=False):
        country_code = self.country_id.code or ''
        if self.country_id and country_code.upper() != 'BR':
            # this ensure other localizations could do what they want
            return super(ResPartner, self)._display_address(
                without_company=False)
        else:
            address_format = (
                self.country_id and self.country_id.address_format or
                "%(street)s\n%(street2)s\n%(city)s"
                " %(state_code)s%(zip)s\n%(country_name)s")
            args = {
                'state_code': self.state_id and self.state_id.code or '',
                'state_name': self.state_id and self.state_id.name or '',
                'country_code': self.country_id and self.country_id.code or '',
                'country_name': self.country_id and self.country_id.name or '',
                'company_name': self.parent_id and self.parent_id.name or '',
                'l10n_br_city_name': self.l10n_br_city_id and
                self.l10n_br_city_id.name or '',
            }
            address_field = ['title', 'street', 'street2', 'zip',
                             'city', 'number', 'district']
            for field in address_field:
                args[field] = getattr(self, field) or ''
            if without_company:
                args['company_name'] = ''
            elif self.parent_id:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)

    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)
    other_inscr_est_lines = fields.One2many(
        'other.inscricoes.estaduais', 'partner_id',
        string=u'Outras Inscrições Estaduais', ondelete='cascade'
    )

    inscr_mun = fields.Char('Inscr. Municipal', size=18)

    suframa = fields.Char('Suframa', size=18)

    legal_name = fields.Char(
        u'Razão Social', size=128,
        help="Nome utilizado em documentos fiscais")

    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', u'Município',
        domain="[('state_id','=',state_id)]")

    district = fields.Char('Bairro', size=32)

    number = fields.Char(u'Número', size=10)

    union_entity_code = fields.Char(string='Union entity code')

    @api.multi
    @api.constrains('cnpj_cpf', 'inscr_est')
    def _check_cnpj_inscr_est(self):
        for record in self:
            domain = []

            # permite cnpj vazio
            if not record.cnpj_cpf:
                return

            allow_cnpj_multi_ie = record.env['ir.config_parameter'].get_param(
                'l10n_br_base_allow_cnpj_multi_ie', default=True)

            if record.parent_id:
                domain += [
                    ('id', 'not in', record.parent_id.ids),
                    ('parent_id', 'not in', record.parent_id.ids)
                ]

            domain += [
                ('cnpj_cpf', '=', record.cnpj_cpf),
                ('id', '!=', record.id)
            ]

            # se encontrar CNPJ iguais
            if record.env['res.partner'].search(domain):

                if allow_cnpj_multi_ie == u'True':
                    for partner in record.env['res.partner'].search(domain):
                        if (partner.inscr_est == record.inscr_est and
                                not record.inscr_est):
                            raise ValidationError(
                                u'Já existe um parceiro cadastrado com esta '
                                u'Inscrição Estadual !')
                else:
                    raise ValidationError(
                        u'Já existe um parceiro cadastrado com este CNPJ !')

    @api.multi
    @api.constrains('cnpj_cpf', 'country_id')
    def _check_cnpj_cpf(self):
        result = True
        for record in self:
            country_code = record.country_id.code or ''
            if record.cnpj_cpf and country_code.upper() == 'BR':
                if record.is_company:
                    if not fiscal.validate_cnpj(record.cnpj_cpf):
                        result = False
                        document = u'CNPJ'
                elif not fiscal.validate_cpf(record.cnpj_cpf):
                    result = False
                    document = u'CPF'
            if not result:
                raise ValidationError(u"{} Invalido!".format(document))

    @api.multi
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
        """
        for record in self:
            result = True
            if record.inscr_est and record.is_company and record.state_id:
                state_code = record.state_id.code or ''
                uf = state_code.lower()
                result = fiscal.validate_ie(uf, record.inscr_est)
            if not result:
                raise ValidationError(u"Inscrição Estadual Invalida!")

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for record in self:
            record.inscr_est = None

    @api.onchange('cnpj_cpf', 'country_id')
    def _onchange_cnpj_cpf(self):
        country = self.country_id.code or ''
        cpf_cnpj = fiscal.format_cpf_cnpj(self.cnpj_cpf, country,
                                          self.is_company)
        if cpf_cnpj:
            self.cnpj_cpf = cpf_cnpj

    @api.onchange('l10n_br_city_id')
    def _onchange_l10n_br_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int l10n_br_city_id: id do l10n_br_city_id digitado.

        return: dicionário com o nome e id do município.
        """
        if self.l10n_br_city_id:
            self.city = self.l10n_br_city_id.name

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])

    def _address_fields(self):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set.
        Extenção para os novos campos do endereço """
        address_fields = super(ResPartner, self)._address_fields()
        return list(address_fields + ['l10n_br_city_id', 'number', 'district'])

    @api.multi
    @api.constrains('other_inscr_est_lines')
    def _check_other_ie_lines(self):
        """Checks if field other insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False.
        """
        for record in self:
            for inscr_est_line in record.other_inscr_est_lines:
                state_code = inscr_est_line.state_id.code or ''
                uf = state_code.lower()
                valid_ie = fiscal.validate_ie(uf, inscr_est_line.inscr_est)
                if not valid_ie:
                    raise ValidationError(u"Inscrição Estadual Invalida!")
                if inscr_est_line.state_id.id == record.state_id.id:
                    raise ValidationError(
                        u"Somente pode existir uma Inscrição"
                        u" Estadual por estado para cada Parceiro!")
                duplicate_ie = record.search([
                    ('state_id', '=', inscr_est_line.state_id.id),
                    ('inscr_est', '=', inscr_est_line.inscr_est)
                ])
                if duplicate_ie:
                    raise ValidationError(
                        u"Inscrição Estadual já usada"
                        u" por %s" % duplicate_ie.name)


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    number = fields.Char(u'Número', size=10)
    street = fields.Char('Street', size=128)
    street2 = fields.Char('Street2', size=128)
    district = fields.Char('Bairro', size=32)
    state_id = fields.Many2one(
        "res.country.state", 'Fed. State',
        change_default=True, domain="[('country_id','=',country_id)]")
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    acc_number = fields.Char("Account Number", size=64, required=False)
    bank = fields.Many2one('res.bank', 'Bank', required=False)
    acc_number_dig = fields.Char('Digito Conta', size=8)
    bra_number = fields.Char(u'Agência', size=8)
    bra_number_dig = fields.Char(u'Dígito Agência', size=8)
    zip = fields.Char('CEP', size=24, change_default=True)
    country_id = fields.Many2one('res.country', 'País', ondelete='restrict')

    @api.multi
    def onchange_partner_id(self, partner_id):
        result = super(ResPartnerBank, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        result['value']['number'] = partner.number
        result['value']['district'] = partner.district
        result['value']['l10n_br_city_id'] = partner.l10n_br_city_id.id
        return result


class OtherInscricoesEstaduais(models.Model):
    _name = 'other.inscricoes.estaduais'

    partner_id = fields.Many2one('res.partner')
    inscr_est = fields.Char(
        size=16, string='Inscr. Estadual', required=True
    )
    state_id = fields.Many2one(
        'res.country.state', 'Estado', required=True
    )

    _sql_constraints = [
        ('other_inscricoes_estaduais_id_uniq',
         'unique (state_id, partner_id)',
         u'O Parceiro já possui uma Inscrição Estadual para esse Estado!')
    ]
