# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api
from openerp.addons.l10n_br_base.tools import fiscal
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"

    legal_name = fields.Char(
        u'Razão Social', size=128,
        help="nome utilizado em documentos fiscais")
    cnpj = fields.Char('CNPJ', size=18)
    inscr_est = fields.Char('Inscr. Estadual/RG', size=16)
    inscr_mun = fields.Char('Inscr. Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio',
        domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char(u'Número', size=10)
    name_surname = fields.Char(u'Nome e sobrenome', size=128,
                               help="Nome utilizado em documentos fiscais")
    cpf = fields.Char('CPF', size=18)
    rg = fields.Char('RG', size=16)

    @api.multi
    @api.constrains('cnpj')
    def _check_cnpj(self):
        for record in self:
            country_code = record.country_id.code or ''
            if record.cnpj and country_code.upper() == 'BR':
                cnpj = re.sub('[^0-9]', '', record.cnpj)
                if not fiscal.validate_cnpj(cnpj):
                    raise ValidationError(_(u'CNPJ inválido!'))
            return True

    @api.multi
    @api.constrains('cpf')
    def _check_cpf(self):
        for record in self:
            country_code = record.country_id.code or ''
            if record.cpf and country_code.upper() == 'BR':
                cpf = re.sub('[^0-9]', '', record.cpf)
                if not fiscal.validate_cpf(cpf):
                    raise ValidationError(_(u'CPF inválido!'))
            return True

    @api.multi
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.
        """
        for record in self:
            result = True
            if record.inscr_est and record.cnpj and record.state_id:
                state_code = record.state_id.code or ''
                uf = state_code.lower()
                result = fiscal.validate_ie(uf, record.inscr_est)
            if not result:
                raise ValidationError(u"Inscrição Estadual Invalida!")

    @api.onchange('cnpj', 'country_id')
    def _onchange_cnpj(self):
        cnpj = None
        country_code = self.country_id.code or ''
        if self.cnpj and country_code.upper() == 'BR':
            val = re.sub('[^0-9]', '', self.cnpj)
            if len(val) == 14:
                cnpj = "%s.%s.%s/%s-%s" % (
                    val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            self.cnpj = cnpj

    @api.onchange('cpf', 'country_id')
    def onchange_mask_cpf(self):
        cpf = None
        country_code = self.country_id.code or ''
        if self.cpf and country_code.upper() == 'BR':
            val = re.sub('[^0-9]', '', self.cpf)
            if len(val) == 11:
                cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
            self.cpf = cpf

    @api.onchange('l10n_br_city_id')
    def onchange_l10n_br_city_id(self):
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
            self.l10n_br_city_id = self.l10n_br_city_id

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])

    @api.multi
    def on_change_partner(self, partner_id):
        result = super(CrmLead, self).on_change_partner(partner_id)

        if partner_id:
            partner = self.pool.get('res.partner').browse(partner_id)
            result['value']['legal_name'] = partner.legal_name
            result['value']['cnpj_cpf'] = partner.cnpj_cpf
            result['value']['inscr_est'] = partner.inscr_est
            result['value']['suframa'] = partner.suframa
            result['value']['number'] = partner.number
            result['value']['district'] = partner.district
            result['value']['l10n_br_city_id'] = partner.l10n_br_city_id.id

        return result

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        result = super(CrmLead, self)._lead_create_contact(
            lead, name, is_company, parent_id)

        value = {
            'number': lead.number,
            'district': lead.district,
            'l10n_br_city_id': lead.l10n_br_city_id.id
        }

        if is_company:
            value.update({
                'legal_name': lead.legal_name,
                'cnpj_cpf': lead.cnpj,
                'inscr_est': lead.inscr_est,
                'inscr_mun': lead.inscr_mun,
                'suframa': lead.suframa,
            })
        else:
            value.update({
                'legal_name': lead.name_surname,
                'cnpj_cpf': lead.cpf,
                'inscr_est': lead.rg,
            })
        if result:
            partner = self.env['res.partner'].browse(result)
            partner.write(value)
        return result
