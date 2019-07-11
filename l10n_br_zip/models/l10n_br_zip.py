# Copyright (C) 2012  Renato Lima (Akretion)                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.addons.l10n_br_base.tools import misc

_logger = logging.getLogger(__name__)

try:
    import pycep_correios
except ImportError:
    _logger.warning("Library PyCEP-Correios not installed !")


class L10nBrZip(models.Model):
    """ Este objeto persiste todos os códigos postais que podem ser
    utilizados para pesquisar e auxiliar o preenchimento dos endereços.
    """
    _name = 'l10n_br.zip'
    _description = 'CEP'
    _rec_name = 'zip_code'

    zip_code = fields.Char(
        string='CEP',
        size=8,
        required=True)

    street_type = fields.Char(
        string='Street Type',
        size=26)

    zip_complement = fields.Char(
        string='Range',
        size=200)

    street = fields.Char(
        string='Logradouro',
        size=72)

    district = fields.Char(
        string='District',
        size=72)

    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country')

    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        domain="[('country_id','=',country_id)]")

    city_id = fields.Many2one(
        comodel_name='res.city',
        string='City',
        required=True,
        domain="[('state_id','=',state_id)]")

    def _set_domain(self, country_id=False, state_id=False,
                    city_id=False, district=False,
                    street=False, zip_code=False):
        domain = []
        if zip_code:
            new_zip = misc.punctuation_rm(zip_code or '')
            domain.append(('zip_code', '=', new_zip))
        else:
            if not state_id or not city_id or len(street or '') == 0:
                raise UserError(
                    _('Necessário informar Estado, município e logradouro'))

            if country_id:
                domain.append(('country_id', '=', country_id))
            if state_id:
                domain.append(('state_id', '=', state_id))
            if city_id:
                domain.append(('city_id', '=', city_id))
            if district:
                domain.append(('district', 'ilike', district))
            if street:
                domain.append(('street', 'ilike', street))

        return domain

    def set_result(self, zip_obj=None):
        if zip_obj:
            if type(zip_obj).__name__ == 'l10n_br.zip.result':
                zip_code = zip_obj.zip
            else:
                zip_code = zip_obj.zip_code

            if len(zip_code) == 8:
                zip_code = '%s-%s' % (zip_code[0:5], zip_code[5:8])
            result = {
                'country_id': zip_obj.country_id.id,
                'state_id': zip_obj.state_id.id,
                'city_id': zip_obj.city_id.id,
                'city': zip_obj.city_id.name,
                'district': zip_obj.district,
                'street': ((zip_obj.street_type or '') +
                           ' ' + (zip_obj.street or '')) if
                zip_obj.street_type else (zip_obj.street or ''),
                'zip': zip_code,
            }
        else:
            result = {}
        return result

    @api.model
    def zip_search(self, obj):

        try:
            domain = self._set_domain(
                country_id=obj.country_id.id,
                state_id=obj.state_id.id,
                city_id=obj.city_id.id,
                district=obj.district,
                street=obj.street,
                zip_code=obj.zip)
        except AttributeError as e:
            raise UserError(
                _('Erro a Carregar Atributo: ') + str(e))

        zip_ids = self.search(domain)

        if len(zip_ids) == 1:
            result = self.set_result(zip_ids[0])
            obj.write(result)
            return True

        elif len(zip_ids) > 1:

            obj_zip_result = self.env['l10n_br.zip.result']
            zip_ids = obj_zip_result.map_to_zip_result(
                zip_ids, obj._name, obj.id)

            return self.create_wizard(
                obj._name,
                obj.id,
                country_id=obj.country_id.id,
                state_id=obj.state_id.id,
                city_id=obj.city_id.id,
                district=obj.district,
                street=obj.street,
                zip_code=obj.zip,
                zip_ids=zip_ids,
            )
        elif not zip_ids and obj.zip:

            zip_str = misc.punctuation_rm(obj.zip)
            try:
                res = pycep_correios.consultar_cep(zip_str)
            except Exception as e:
                raise UserError(
                    _('Erro no PyCEP-Correios : ') + str(e))

            if res:
                # Search Brazil id
                country = self.env['res.country'].search(
                    [('code', '=', 'BR')], limit=1)

                # Search state with state_code and country id
                state = self.env['res.country.state'].search([
                    ('code', '=', res['uf']),
                    ('country_id', '=', country.id)], limit=1)

                # search city with name and state
                city = self.env['res.city'].search([
                    ('name', '=', res['cidade']),
                    ('state_id.id', '=', state.id)], limit=1)

                values = {
                    'zip_code': zip_str,
                    'street': res['end'],
                    'zip_complement': res['complemento2'],
                    'district': res['bairro'],
                    'city_id': city.id or False,
                    'state_id': state.id or False,
                    'country_id': country.id or False,
                }

                # Create zip object
                self.env['l10n_br.zip'].create(values)

                zip_ids = self.search(domain)
                result = self.set_result(zip_ids[0])
                obj.write(result)
                return True

    def create_wizard(self, object_name, address_id, country_id=False,
                      state_id=False, city_id=False,
                      district=False, street=False, zip_code=False,
                      zip_ids=False):
        context = dict(self.env.context)
        context.update({
            'zip': zip_code,
            'street': street,
            'district': district,
            'country_id': country_id,
            'state_id': state_id,
            'city_id': city_id,
            'zip_ids': zip_ids,
            'address_id': address_id,
            'object_name': object_name})

        result = {
            'name': 'Zip Search',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_br.zip.search',
            'view_id': False,
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'nodestroy': True,
        }

        return result
