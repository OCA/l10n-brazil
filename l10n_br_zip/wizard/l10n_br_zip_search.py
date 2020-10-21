# Copyright (C) 2011  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class L10nBrZipSearch(models.TransientModel):
    _name = 'l10n_br.zip.search'
    _description = 'Zipcode Search'

    zip = fields.Char(
        string='CEP',
        size=8)

    street = fields.Char(
        string='Logradouro',
        size=72)

    district = fields.Char(
        string='District',
        size=72)

    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country')

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]")

    city_id = fields.Many2one(
        comodel_name='res.city',
        string='Cidade',
        domain="[('state_id', '=', state_id)]")

    zip_ids = fields.Many2many(
        comodel_name='l10n_br.zip.result',
        relation='zip_search',
        column1='zip_search_id',
        column2='zip_id',
        string='CEPs',
        readonly=False)

    state = fields.Selection(
        selection=[('init', 'init'),
                   ('done', 'done')],
        string='state',
        readonly=True,
        default='init')

    address_id = fields.Integer(
        string='Id do objeto',
        invisible=True)

    object_name = fields.Char(
        string='Nome do Objeto',
        size=100,
        invisible=True)

    @api.model
    def create(self, vals):
        result = super(L10nBrZipSearch, self).create(vals)
        # TO DO : FIX IT
        #  context.update({'search_id': result})
        return result

    @api.multi
    def default_get(self, fields_list):
        data = super(L10nBrZipSearch, self).default_get(fields_list)

        context = dict(self._context or {})
        data['zip'] = context.get('zip', False)
        data['street'] = context.get('street', False)
        data['district'] = context.get('district', False)
        data['country_id'] = context.get('country_id', False)
        data['state_id'] = context.get('state_id', False)
        data['city_id'] = context.get('city_id', False)
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
            city_id=data['city_id'][0],
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

    @api.multi
    def zip_new_search(self):
        data = self.read()[0]
        self.ensure_one()
        self.write({'state': 'init',
                    'zip_ids': [[6, 0, []]]})

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
        comodel_name='l10n_br.zip',
        string='Zipcode',
        readonly=True,
        invisible=True)

    search_id = fields.Many2one(
        comodel_name='l10n_br.zip.search',
        string='Search',
        readonly=True,
        invisible=True)

    address_id = fields.Integer(
        string='Id do objeto',
        invisible=True)

    object_name = fields.Char(
        string='Nome do objeto',
        size=100,
        invisible=True)

    # ZIPCODE data to be shown
    zip = fields.Char(
        string='CEP',
        size=9,
        readonly=True)

    street = fields.Char(
        string='Logradouro',
        size=72,
        readonly=True)

    street_type = fields.Char(
        string='Tipo',
        size=26,
        readonly=True)

    district = fields.Char(
        string='District',
        size=72,
        readonly=True)

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        readonly=True)

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]",
        readonly=True)

    city_id = fields.Many2one(
        comodel_name='res.city',
        string='City',
        required=True,
        domain="[('state_id', '=', state_id)]",
        readonly=True)

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
