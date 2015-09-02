# -*- encoding: utf-8 -*-
##############################################################################
#
#    Address from Brazilian Localization ZIP by Correios to Odoo
#    Copyright (C) 2015 KMEE (http://www.kmee.com.br)
#    @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
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

from openerp import models, api
from openerp.tools.translate import _
from openerp.exceptions import Warning

from suds.client import Client, TransportError
from suds import WebFault


class WebServiceClient(object):

    @api.one
    def get_address(self):

        if not self.zip:
            return

        zip_str = self.zip.replace('-', '')

        if len(zip_str) != 8:
            raise Warning(_('Error!'), _('Invalid zip length'))

        if not self.env['l10n_br.zip'].search([('zip', '=', zip_str)]):

            # SigepWeb webservice url
            url_prod = 'https://apps.correios.com.br/SigepMasterJPA' \
                       '/AtendeClienteService/AtendeCliente?wsdl'

            try:

                # Connect Brazil Correios webservice
                res = Client(url_prod).service.consultaCEP(zip_str)

                # Search state with state_code
                state_ids = self.env['res.country.state'].search(
                    [('code', '=', str(res.uf))])

                # city name
                city_name = str(res.cidade.encode('utf8'))

                # search city with name and state
                city_ids = self.env['l10n_br_base.city'].search([
                    ('name', '=', city_name),
                    ('state_id.id', 'in', state_ids.ids)])

                # Search Brazil id
                country_ids = self.env['res.country'].search(
                    [('code', '=', 'BR')])

                values = {
                    'zip': zip_str,
                    'street': str(res.end.encode('utf8')) if res.end else '',
                    'district': str(res.bairro.encode('utf8')) if res.bairro
                    else '',
                    'street_type': str(res.complemento.encode('utf8')) if res.complemento
                    else '',
                    'l10n_br_city_id': city_ids.ids[0] if city_ids else False,
                    'state_id': state_ids.ids[0] if state_ids else False,
                    'country_id': country_ids.ids[0] if country_ids else False,
                }

                # Create zip object
                self.env['l10n_br.zip'].create(values)

            except TransportError as e:
                raise Warning(_('Error!'), e.message)
            except WebFault as e:
                raise Warning(_('Error!'), e.message)

