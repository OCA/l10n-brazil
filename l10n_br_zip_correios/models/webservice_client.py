# -*- coding: utf-8 -*-
# Copyright (C) 2015 KMEE (http://www.kmee.com.br)
# @author Michell Stuttgart <michell.stuttgart@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from odoo.exceptions import Warning as UserError
from odoo.tools.translate import _

try:
    from suds import WebFault
    from suds.client import Client, TransportError
except ImportError:
    raise UserError(_(u'Erro!'), _(u"Biblioteca Suds não instalada!"))

try:
    # to pip install suds (version: 0.4)
    from suds.client import TransportError
except ImportError as ex:
    # to apt-get install python-suds (version: 0.7~git20150727.94664dd-3)
    from suds.transport import TransportError

_logger = logging.getLogger(__name__)


class WebServiceClient(object):
    """Address from Brazilian Localization ZIP by Correios to Odoo"""

    def __init__(self, l10n_br_zip_record):
        self.obj_zip = l10n_br_zip_record
        self.url = 'https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl' # noqa

    def search_zip_code(self, cep):
        return Client(self.url).service.consultaCEP(cep)

    def get_address(self, zip_str):

        if not self.obj_zip.env['l10n_br.zip'].search(
                [('zip_code', '=', zip_str)]):

            try:

                # Connect Brazil Correios webservice
                res = self.search_zip_code(zip_str)

                # Search Brazil id
                country_ids = self.obj_zip.env['res.country'].search(
                    [('code', '=', 'BR')])

                # Search state with state_code and country id
                state_ids = self.obj_zip.env['res.country.state'].search([
                    ('code', '=', str(res.uf)),
                    ('country_id.id', 'in', country_ids.ids)])

                # city name
                city_name = str(res.cidade.encode('utf8'))

                # search city with name and state
                city_ids = self.obj_zip.env['l10n_br_base.city'].search([
                    ('name', '=', city_name),
                    ('state_id.id', 'in', state_ids.ids)])

                values = {
                    'zip_code': zip_str,
                    'street': str(
                        res.end.encode('utf8')) if res.end else '',
                    'district': str(
                        res.bairro.encode('utf8')) if res.bairro
                    else '',
                    'street_type': str(
                        res.complemento.encode('utf8')) if res.complemento
                    else '',
                    'l10n_br_city_id': city_ids.ids[
                        0] if city_ids else False,
                    'state_id': state_ids.ids[0] if state_ids else False,
                    'country_id': country_ids.ids[
                        0] if country_ids else False,
                }

                # Create zip object
                return self.obj_zip.env['l10n_br.zip'].create(values)

            except TransportError as e:
                _logger.error(e.message, exc_info=True)
                raise UserError(_('Error!'), e.message)
            except WebFault as e:
                _logger.error(e.message, exc_info=True)
                raise UserError(_('Error!'), e.message)

        else:
            return None
