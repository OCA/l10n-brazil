# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
#    Akretion
#    Copyright (C) Akretion (<http://www.akretion.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re

from openerp.osv import fields, orm


#TODO Migrar para nova API ainda não foi feito por causa da função reverse
class ResCompany(orm.Model):
    _inherit = 'res.company'

    def _get_l10n_br_data(self, cr, uid, ids, field_names, arg, context=None):
        """ Read the l10n_br specific functional fields. """
        result = {}
        companies = self.browse(cr, uid, ids, context=context)
        for company in companies:
            result[company.id] = {
                'legal_name': company.partner_id.legal_name,
                'cnpj_cpf': company.partner_id.cnpj_cpf,
                'inscr_est': company.partner_id.inscr_est,
                'inscr_mun': company.partner_id.inscr_mun,
                'suframa': company.partner_id.suframa
            }
        return result

    def _set_l10n_br_data(self, cr, uid, company_id, name,
                            value, arg, context=None):
        """ Write the l10n_br specific functional fields. """
        company = self.browse(cr, uid, company_id, context=context)
        if company.partner_id:
            part_obj = self.pool.get('res.partner')
            part_obj.write(cr, uid, company.partner_id.id,
                {name: value or False}, context=context)
        return True

    def _get_address_data(self, cr, uid, ids, field_names, arg, context=None):
        return super(ResCompany, self)._get_address_data(
            cr, uid, ids, field_names, arg, context=context)

    def _set_address_data(self, cr, uid, company_id, name,
                            value, arg, context=None):
        return super(ResCompany, self)._set_address_data(
            cr, uid, company_id, name, value, arg, context=context)

    _columns = {
        'cnpj_cpf': fields.function(
            _get_l10n_br_data, fnct_inv=_set_l10n_br_data, size=18,
            type='char', string='CNPJ/CPF', multi='l10n_br'),
        'inscr_est': fields.function(
            _get_l10n_br_data, fnct_inv=_set_l10n_br_data, size=16,
            type='char', string='Inscr. Estadual', multi='l10n_br'),
        'inscr_mun': fields.function(
            _get_l10n_br_data, fnct_inv=_set_l10n_br_data, size=18,
            type='char', string='Inscr. Municipal', multi='l10n_br'),
        'suframa': fields.function(
            _get_l10n_br_data, fnct_inv=_set_l10n_br_data, size=18,
            type='char', string='Suframa', multi='l10n_br'),
        'legal_name': fields.function(
            _get_l10n_br_data, fnct_inv=_set_l10n_br_data, size=128,
            type='char', string=u'Razão Social', multi='l10n_br'),
        'l10n_br_city_id': fields.function(
            _get_address_data, fnct_inv=_set_address_data, type='many2one',
            relation='l10n_br_base.city', string="City", multi='address'),
        'district': fields.function(
            _get_address_data, fnct_inv=_set_address_data, size=32,
            type='char', string="Bairro", multi='address'),
        'number': fields.function(
            _get_address_data, fnct_inv=_set_address_data, size=10,
            type='char', string="Número", multi='address'),
    }

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, cnpj_cpf):
        result = {'value': {}}
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            result['value'].update({'cnpj_cpf': cnpj_cpf})
        return result

    def onchange_l10n_br_city_id(self, cr, uid, ids, l10n_br_city_id):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int l10n_br_city_id: id do l10n_br_city_id digitado.

        return: dicionário com o nome e id do município.
        """
        result = {'value': {'city': False, 'l10n_br_city_id': False}}

        if not l10n_br_city_id:
            return result

        obj_city = self.pool.get('l10n_br_base.city').read(
            cr, uid, l10n_br_city_id, ['name', 'id'])

        if obj_city:
            result['value']['city'] = obj_city['name']
            result['value']['l10n_br_city_id'] = obj_city['id']

        return result

    def onchange_mask_zip(self, cr, uid, ids, code_zip):

        result = {'value': {'zip': False}}

        if not code_zip:
            return result

        val = re.sub('[^0-9]', '', code_zip)

        if len(val) == 8:
            code_zip = "%s-%s" % (val[0:5], val[5:8])
            result['value']['zip'] = code_zip
        return result
