# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>).
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

from openerp.osv import fields, osv

class res_company(osv.osv):
    _inherit = 'res.company'
    
    def _get_address_data(self, cr, uid, ids, field_names, arg, context=None):
        return super(res_company,self)._get_address_data(cr, uid, ids, field_names, arg, context=context)
    
    def _set_address_data(self, cr, uid, company_id, name, value, arg, context=None):
        return super(res_company,self)._set_address_data(cr, uid, company_id, name, value, arg, context=context)

    _columns = {
        'l10n_br_city_id': fields.function(_get_address_data, fnct_inv=_set_address_data, type='many2one', relation='l10n_br_base.city', string="City", multi='address'),
        'district': fields.function(_get_address_data, fnct_inv=_set_address_data, size=32, type='char', string="Bairro", multi='address'),
        'number': fields.function(_get_address_data, fnct_inv=_set_address_data, size=10, type='char', string="Número", multi='address'),
    }
    
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