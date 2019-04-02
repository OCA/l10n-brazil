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

        if not self.obj_zip.env['l10n_br.zip'].search([('zip', '=', zip_str)]):

            try:
                # Connect Brazil Correios webservice
                res = self.search_zip_code(zip_str)

                # Search Brazil id
                country = self.obj_zip.env['res.country'].search(
                    [('code', '=', 'BR')], limit=1)

                # Search state with state_code and country id
                state = self.obj_zip.env['res.country.state'].search([
                    ('code', '=', res.uf),
                    ('country_id', '=', country.id)], limit=1)

                # search city with name and state
                city = self.obj_zip.env['res.city'].search([
                    ('name', '=', res.cidade),
                    ('state_id.id', '=', state.id)], limit=1)

                values = {
                    'zip': zip_str,
                    'street': res.end,
                    'district': res.bairro,
                    'city_id': city.id or False,
                    'state_id': state.id or False,
                    'country_id': country.id or False,
                }

                # Create zip object
                return self.obj_zip.env['l10n_br.zip'].create(values)

            except TransportError as e:
                _logger.error(str(e), exc_info=True)
                raise UserError(str(e))
            except WebFault as e:
                _logger.error(str(e), exc_info=True)
                raise UserError(str(e))

        else:
            return None
