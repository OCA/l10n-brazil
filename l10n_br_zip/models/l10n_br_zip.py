# -*- coding: utf-8 -*-
# Copyright (C) 2012  Renato Lima (Akretion)                                  #
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import except_orm
from openerp.exceptions import Warning as UserError


class L10nBrZip(models.Model):
    """ Este objeto persiste todos os códigos postais que podem ser
    utilizados para pesquisar e auxiliar o preenchimento dos endereços.
    """
    _name = 'l10n_br.zip'
    _description = 'CEP'
    _rec_name = 'zip'

    zip = fields.Char('CEP', size=8, required=True)
    street_type = fields.Char('Tipo', size=26)
    street = fields.Char('Logradouro', size=72)
    district = fields.Char('Bairro', size=72)
    country_id = fields.Many2one('res.country', u'País')
    state_id = fields.Many2one(
        'res.country.state', 'Estado',
        domain="[('country_id','=',country_id)]")
    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Cidade',
        required=True, domain="[('state_id','=',state_id)]")

    def set_domain(self, country_id=False, state_id=False,
                   l10n_br_city_id=False, district=False,
                   street=False, zip_code=False):
        domain = []
        if zip_code:
            new_zip = re.sub('[^0-9]', '', zip_code or '')
            domain.append(('zip', '=', new_zip))
        else:
            if not state_id or not l10n_br_city_id or \
                    len(street or '') == 0:
                raise except_orm(
                    u'Parâmetros insuficientes',
                    u'Necessário informar Estado, município e logradouro')

            if country_id:
                domain.append(('country_id', '=', country_id))
            if state_id:
                domain.append(('state_id', '=', state_id))
            if l10n_br_city_id:
                domain.append(('l10n_br_city_id', '=', l10n_br_city_id))
            if district:
                domain.append(('district', 'ilike', district))
            if street:
                domain.append(('street', 'ilike', street))

        return domain

    def set_result(self, zip_obj=None):
        if zip_obj:
            zip_code = zip_obj.zip
            if len(zip_code) == 8:
                zip_code = '%s-%s' % (zip_code[0:5], zip_code[5:8])
            result = {
                'country_id': zip_obj.country_id.id,
                'state_id': zip_obj.state_id.id,
                'l10n_br_city_id': zip_obj.l10n_br_city_id.id,
                'district': zip_obj.district,
                'street': ((zip_obj.street_type or '') +
                           ' ' + (zip_obj.street or '')) if
                zip_obj.street_type else (zip_obj.street or ''),
                'zip': zip_code,
            }
        else:
            result = {}
        return result

    def zip_search_multi(self, country_id=False,
                         state_id=False, l10n_br_city_id=False,
                         district=False, street=False, zip_code=False):
        domain = self.set_domain(
            country_id=country_id,
            state_id=state_id,
            l10n_br_city_id=l10n_br_city_id,
            district=district,
            street=street,
            zip_code=zip_code)
        return self.search(domain)

    @api.multi
    def zip_search(self, obj):

        zip_ids = self.zip_search_multi(
            country_id=obj.country_id.id,
            state_id=obj.state_id.id,
            l10n_br_city_id=obj.l10n_br_city_id.id,
            district=obj.district,
            street=obj.street,
            zip_code=obj.zip,
        )

        if len(zip_ids) == 1:
            result = self.set_result(zip_ids[0])
            obj.write(result)
            return True
        else:
            if len(zip_ids) > 1:
                obj_zip_result = self.env['l10n_br.zip.result']
                zip_ids = obj_zip_result.map_to_zip_result(
                    zip_ids, obj._name, obj.id)

                return self.create_wizard(
                    obj._name,
                    obj.id,
                    country_id=obj.country_id.id,
                    state_id=obj.state_id.id,
                    l10n_br_city_id=obj.l10n_br_city_id.id,
                    district=obj.district,
                    street=obj.street,
                    zip_code=obj.zip,
                    zip_ids=[zip.id for zip in zip_ids]
                )
            else:
                raise UserError(_('Nenhum registro encontrado'))

    def create_wizard(self, object_name, address_id, country_id=False,
                      state_id=False, l10n_br_city_id=False,
                      district=False, street=False, zip_code=False,
                      zip_ids=False):
        context = dict(self.env.context)
        context.update({
            'zip': zip_code,
            'street': street,
            'district': district,
            'country_id': country_id,
            'state_id': state_id,
            'l10n_br_city_id': l10n_br_city_id,
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
