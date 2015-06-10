# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 Gabriel C. Stabel                                        #
# Copyright (C) 2009 Renato Lima (Akretion)                                   #
# Copyright (C) 2012 Raphaël Valyi (Akretion)                                 #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

import re

from openerp import models, fields, api
from openerp.addons.l10n_br_base.tools import fiscal
from openerp.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _display_address(self, address, without_company=False):
        country_code = address.country_id.code or ''
        if address.country_id and country_code.upper() != 'BR':
            # this ensure other localizations could do what they want
            return super(ResPartner, self)._display_address(
                address, without_company=False)
        else:
            address_format = (
                address.country_id and address.country_id.address_format
                or "%(street)s\n%(street2)s\n%(city)s"
                " %(state_code)s%(zip)s\n%(country_name)s")
            args = {
                'state_code': address.state_id and
                address.state_id.code or '',
                'state_name': address.state_id and
                address.state_id.name or '',
                'country_code': address.country_id and
                address.country_id.code or '',
                'country_name': address.country_id and
                address.country_id.name or '',
                'company_name': address.parent_id and
                address.parent_id.name or '',
                'l10n_br_city_name': address.l10n_br_city_id and
                address.l10n_br_city_id.name or '',
            }
            address_field = ['title', 'street', 'street2', 'zip',
                             'city', 'number', 'district']
            for field in address_field:
                args[field] = getattr(address, field) or ''
            if without_company:
                args['company_name'] = ''
            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)
    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)
    inscr_mun = fields.Char('Inscr. Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    legal_name = fields.Char(
        u'Razão Social', size=128,
        help="Nome utilizado em documentos fiscais")
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char(u'Número', size=10)

    _sql_constraints = [
        ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)',
         u'Já existe um parceiro cadastrado com este CPF/CNPJ !'),
        ('res_partner_inscr_est_uniq', 'unique (inscr_est)',
         u'Já existe um parceiro cadastrado com esta Inscrição Estadual/RG !')
    ]

    @api.one
    @api.constrains('cnpj_cpf')
    def _check_cnpj_cpf(self):
        result = True
        if self.cnpj_cpf:
            if self.is_company:
                if not fiscal.validate_cnpj(self.cnpj_cpf):
                    result = False
                    document = u'CNPJ'
            elif not fiscal.validate_cpf(self.cnpj_cpf):
                result = False
                document = u'CPF'
        if not result:
            raise ValidationError(u"{} Invalido!".format(document))

    def _validate_ie_param(self, uf, inscr_est):
        result = True
        try:
            mod = __import__(
                'openerp.addons.l10n_br_base.tools.fiscal',
                globals(), locals(), 'fiscal')

            validate = getattr(mod, 'validate_ie_%s' % uf)
            if not validate(inscr_est):
                result = False
        except AttributeError:
            if not fiscal.validate_ie_param(uf, inscr_est):
                result = False
        return result

    @api.one
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
        """
        result = True
        if self.inscr_est == 'ISENTO' or self.is_company:
            state_code = self.state_id.code or ''
            uf = state_code.lower()
            result = self._validate_ie_param(uf, self.inscr_est)
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

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])

    @api.cr_uid_context
    def _address_fields(self, cr, uid, context=None):
        """ Returns the list of address fields that are synced from the parent
        when the `use_parent_address` flag is set.
        Extenção para os novos campos do endereço """
        address_fields = super(ResPartner, self)._address_fields(
            cr, uid, context=context)
        return list(address_fields + ['l10n_br_city_id', 'number', 'district'])


class ResPartnerBank(models.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias no Brasil."""
    _inherit = 'res.partner.bank'

    number = fields.Char(u'Número', size=10)
    street2 = fields.Char('Street2', size=128)
    district = fields.Char('Bairro', size=32)
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    acc_number = fields.Char("Account Number", size=64, required=False)
    bank = fields.Many2one('res.bank', 'Bank', required=False)
    acc_number_dig = fields.Char('Digito Conta', size=8)
    bra_number = fields.Char(u'Agência', size=8)
    bra_number_dig = fields.Char(u'Dígito Agência', size=8)

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

    @api.multi
    def onchange_partner_id(self, partner_id):
        result = super(ResPartnerBank, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        result['value']['number'] = partner.number
        result['value']['district'] = partner.district
        result['value']['l10n_br_city_id'] = partner.l10n_br_city_id.id
        return result
