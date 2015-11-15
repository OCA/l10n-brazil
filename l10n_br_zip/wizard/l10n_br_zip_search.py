# -*- coding: utf-8 -*-
###############################################################################
#
# Copyright (C) 2011  Renato Lima - Akretion
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from openerp import models, fields, api


class L10nBrZipSearch(models.TransientModel):
    _name = 'l10n_br.zip.search'
    _description = 'Zipcode Search'

    zip = fields.Char('CEP', size=8)
    street = fields.Char('Logradouro', size=72)
    district = fields.Char('Bairro', size=72)
    country_id = fields.Many2one('res.country', 'Country')
    state_id = fields.Many2one(
        "res.country.state", 'Estado',
        domain="[('country_id','=',country_id)]")
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Cidade',
        domain="[('state_id','=',state_id)]")
    zip_ids = fields.Many2many(
        'l10n_br.zip.result', 'zip_search', 'zip_search_id',
        'zip_id', 'CEP', readonly=False)
    state = fields.Selection(
        [('init', 'init'), ('done', 'done')],
        'state', readonly=True, default='init')
    address_id = fields.Integer('Id do objeto', invisible=True)
    object_name = fields.Char('Nome do bjeto', size=100, invisible=True)

    def create(self, cr, uid, vals, context):
        result = super(L10nBrZipSearch, self).create(cr, uid, vals, context)
        context.update({'search_id': result})
        return result

    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        data = super(L10nBrZipSearch, self).default_get(
            cr, uid, fields_list, context)

        data['zip'] = context.get('zip', False)
        data['street'] = context.get('street', False)
        data['district'] = context.get('district', False)
        data['country_id'] = context.get('country_id', False)
        data['state_id'] = context.get('state_id', False)
        data['l10n_br_city_id'] = context.get('l10n_br_city_id', False)
        data['address_id'] = context.get('address_id', False)
        data['object_name'] = context.get('object_name', False)

        data['zip_ids'] = context.get('zip_ids', False)
        data['state'] = 'done'

        return data

    @api.one
    def zip_search(self):
        data = self
        obj_zip = self.env['l10n_br.zip']
        obj_zip_result = self.env['l10n_br.zip.result']
        domain = obj_zip.set_domain(
            country_id=data['country_id'][0],
            state_id=data['state_id'][0],
            l10n_br_city_id=data['l10n_br_city_id'][0],
            district=data['district'],
            street=data['street'],
            zip=data['zip']
        )

        # Search zips
        zips = obj_zip.search(domain)
        # MAP zip to zip.search.result
        zip_result_ids = obj_zip_result.map_to_zip_result(
            zips.ids, data['object_name'], data['address_id'])
        self.write(
            {'state': 'done', 'zip_ids': [[6, 0, zip_result_ids]]})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br.zip.search',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': data['id'],
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True,
        }

    def zip_new_search(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        self.write(cr, uid, ids,
                   {'state': 'init',
                    'zip_ids': [[6, 0, []]]}, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_br.zip.search',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': data['id'],
            'views': [(False, 'form')],
            'target': 'new',
            'nodestroy': True
        }


class L10nBrZipResult(models.TransientModel):
    _name = 'l10n_br.zip.result'
    _description = 'Zipcode result'

    zip_id = fields.Many2one(
        'l10n_br.zip', 'Zipcode', readonly=True, invisible=True)
    search_id = fields.Many2one(
        'l10n_br.zip.search', 'Search', readonly=True, invisible=True)
    address_id = fields.Integer('Id do objeto', invisible=True)
    object_name = fields.Char('Nome do bjeto', size=100, invisible=True)
    # ZIPCODE data to be shown
    zip = fields.Char('CEP', size=9, readonly=True)
    street = fields.Char('Logradouro', size=72, readonly=True)
    street_type = fields.Char('Tipo', size=26, readonly=True)
    district = fields.Char('Bairro', size=72, readonly=True)
    country_id = fields.Many2one('res.country', 'Country', readonly=True)
    state_id = fields.Many2one('res.country.state', 'Estado',
                               domain="[('country_id', '=', country_id)]",
                               readonly=True)
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Cidade', required=True,
        domain="[('state_id', '=', state_id)]", readonly=True)

    def map_to_zip_result(self, zip_data, object_name, address_id):
        obj_zip = self.env['l10n_br.zip']
        result = []

        for zip_read in zip_data:
            zip_data = obj_zip.set_result(zip_read)
            zip_result_data = zip_data
            zip_result_data['object_name'] = object_name
            zip_result_data['address_id'] = address_id

            zip_result_id = self.create(zip_result_data)
            result.append(zip_result_id)
        return result

    @api.one
    def zip_select(self):
        data = self
        address_id = data['address_id']
        object_name = data['object_name']
        if address_id and object_name:
            obj = self.env[object_name].browse(address_id)
            obj_zip = self.env['l10n_br.zip']
            result = obj_zip.set_result(data)
            obj.write(result)
        return True
