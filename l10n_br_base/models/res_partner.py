# -*- coding: utf-8 -*-
# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# Copyright (C) 2018 Luis Felipe Mileo (KMEE INFORMATICA LTDA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from ..tools import fiscal
from ..tools.misc import punctuation_rm
from ..constante_tributaria import (
    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE,
    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE,
    INDICADOR_IE_DESTINATARIO,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_SIMPLES,
)


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

    @api.depends('cnpj_cpf')
    def _compute_tipo_pessoa(self):
        for record in self:
            if not record.cnpj_cpf:
                record.tipo_pessoa = 'I'
                record.cnpj_cpf_raiz = ''
                continue

            if record.cnpj_cpf[:2] == 'EX':
                record.tipo_pessoa = 'E'
                record.contribuinte = \
                    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE
                record.cnpj_cpf_raiz = record.cnpj_cpf

            elif len(record.cnpj_cpf) == 18:
                record.tipo_pessoa = 'J'
                record.contribuinte = \
                    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE
                record.cnpj_cpf_raiz = record.cnpj_cpf[:10]

            else:
                record.tipo_pessoa = 'F'
                record.contribuinte = \
                    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE
                record.cnpj_cpf_raiz = record.cnpj_cpf

            record.cnpj_cpf_numero = \
                punctuation_rm(record.cnpj_cpf)

    @api.depends('eh_consumidor_final', 'street', 'number', 'street2',
                 'district', 'l10n_br_city_id', 'zip', 'customer',
                 'supplier')
    def _compute_exige_cadastro_completo(self):
        for record in self:
            if not record.eh_consumidor_final or \
                    record.customer:
                record.exige_cnpj_cpf = True
                record.exige_endereco = True
                continue

            record.exige_cnpj_cpf = False

            if (record.street or record.number or
                    record.stree2 or
                    record.district or record.zip):
                record.exige_endereco = True
            else:
                record.exige_endereco = False

    @api.depends('street', 'number', 'street2', 'district',
                 'l10n_br_city_id', 'zip')
    def _compute_endereco_completo(self):
        for record in self:
            if not record.street:
                record.endereco_completo = ''
                continue

            endereco = record.street
            endereco += ', '
            endereco += record.number

            if record.stree2:
                endereco += ' - '
                endereco += record.stree2

            endereco += ' - '
            endereco += record.district
            endereco += ' - '
            endereco += record.l10n_br_city.name
            endereco += '-'
            endereco += record.l10n_br_city.uf
            endereco += ' - '
            endereco += record.zip
            record.endereco_completo = endereco

    contribuinte = fields.Selection(
        selection=INDICADOR_IE_DESTINATARIO,
        string='Contribuinte',
        # required=True,
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        index=True,
        help='''Para records estrangeiros, usar EX9999,
        onde 9999 é um número a sua escolha'''
    )
    cnpj_cpf_raiz = fields.Char(
        string='Raiz do CNPJ/CPF',
        size=14,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True,
    )
    cnpj_cpf_numero = fields.Char(
        string='CNPJ/CPF (somente números)',
        size=14,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True,
    )
    tipo_pessoa = fields.Char(
        string='Tipo pessoa',
        size=1,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True
    )

    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)

    inscr_mun = fields.Char('Inscr. Municipal', size=18)

    suframa = fields.Char('Suframa', size=18)

    legal_name = fields.Char(
        u'Razão Social', size=60,
        help="Nome utilizado em documentos fiscais"
    )
    fantasia = fields.Char(
        string='Fantasia',
        size=60,
        index=True
    )

    l10n_br_city_id = fields.Many2one(
        comodel_name='l10n_br_base.city',
        string=u'Município',
    )

    district = fields.Char(string='Bairro', size=32)

    number = fields.Char(string=u'Número', size=10)

    endereco_completo = fields.Char(
        string='Endereço',
        compute='_compute_endereco_completo',
    )
    exige_cnpj_cpf = fields.Boolean(
        comodel_name='Exige CNPJ/CPF?',
        compute='_compute_exige_cadastro_completo',
    )
    exige_endereco = fields.Boolean(
        comodel_name='Exige endereço?',
        compute='_compute_exige_cadastro_completo',
    )
    eh_orgao_publico = fields.Boolean(
        string='É órgão público?',
    )
    eh_cooperativa = fields.Boolean(
        string='É cooperativa?',
    )
    eh_sindicato = fields.Boolean(
        string='É sindicato?',
    )
    eh_consumidor_final = fields.Boolean(
        string='É consumidor final?',
    )
    eh_convenio = fields.Boolean(
        string='É convênio?',
    )
    eh_transportadora = fields.Boolean(
        string='É transportadora?'
    )
    eh_grupo = fields.Boolean(
        string='É grupo?',
        index=True,
    )
    im = fields.Char(
        string='Inscrição municipal',
        size=14
    )
    suframa = fields.Char(
        string='SUFRAMA',
        size=12
    )
    rntrc = fields.Char(
        string='RNTRC',
        size=15
    )
    cei = fields.Char(
        string='CEI',
        size=15
    )
    rg_numero = fields.Char(
        string='RG',
        size=14
    )
    rg_orgao_emissor = fields.Char(
        string='Órgão emisssor do RG',
        size=20
    )
    rg_data_expedicao = fields.Date(
        string='Data de expedição do RG'
    )
    crc = fields.Char(
        string='Conselho Regional de Contabilidade',
        size=14
    )
    crc_uf = fields.Many2one(
        comodel_name='res.country.state',
        string='UF do CRC',
        ondelete='restrict'
    )
    profissao = fields.Char(
        string='Cargo',
        size=40
    )
    pais_nacionalidade_id = fields.Many2one(
        comodel_name='res.country',
        string='Nacionalidade',
        ondelete='restrict'
    )
    codigo_sindical = fields.Char(
        comodel_name='Código sindical',
        size=30
    )
    codigo_ans = fields.Char(
        comodel_name='Código ANS',
        size=6
    )
    transportadora_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transportadora',
        ondelete='restrict',
        domain=[('eh_transportadora', '=', True)]
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
        index=True,
    )
    estado = fields.Char(
        string='Estado',
        related='state_id.code',
        store=True,
        index=True,
    )

    @api.onchange('l10n_br_city_id')
    def onchange_l10n_br_city_id(self):
        if self.l10n_br_city_id and self.l10n_br_city_id.cep_unico:
            self.zip = self.l10n_br_city_id.cep_unico

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

        if not self.env['ir.config_parameter'].get_param(
                'l10n_br_base_check_cnpj') == u'True':
            return

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
    @api.constrains('inscr_est', 'state_id')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
        """

        if not self.env['ir.config_parameter'].get_param(
                'l10n_br_base_check_ie') == u'1':
            return

        for record in self:
            result = True
            if record.inscr_est and record.is_company and record.state_id:
                state_code = record.state_id.code or ''
                uf = state_code.lower()
                result = fiscal.validate_ie(uf, record.inscr_est)
            if not result:
                raise ValidationError(u"Inscrição Estadual Invalida!")

    @api.onchange('cnpj_cpf', 'country_id')
    def _onchange_cnpj_cpf(self):
        cnpj_cpf = None
        country_code = self.country_id.code or ''
        if self.cnpj_cpf and country_code.upper() == 'BR':
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if self.is_company and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s" % (
                    val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif not self.is_company and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s" % (
                    val[0:3], val[3:6], val[6:9], val[9:11])
            if cnpj_cpf:
                self.cnpj_cpf = cnpj_cpf

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

    @api.onchange('l10n_br_city_id')
    def _onchange_city(self):
        self.state_id = self.l10n_br_city_id.state_id
        self.country_id = self.l10n_br_city_id.country_id

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
        change_default=True,
    )
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

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])
