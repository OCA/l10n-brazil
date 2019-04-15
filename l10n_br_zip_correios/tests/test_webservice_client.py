# -*- coding: utf-8 -*-
# Copyright (C) 2016 Aldo Soares - MultidadosTI
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import mock
from suds import WebFault
from suds.client import TransportError

from odoo.tests.common import TransactionCase
from odoo.exceptions import Warning as UserError

from ..models.webservice_client import WebServiceClient


class TestWebServiceClient(TransactionCase):

    @mock.patch('openerp.addons.l10n_br_zip_correios.models.'
                'webservice_client.WebServiceClient.search_zip_code')
    def test_search_zip_code(self, mock_api_call):

        web_client = WebServiceClient(self.env['l10n_br.zip'])

        mock_api_call.side_effect = WebFault("", "")
        self.assertRaises(WebFault, web_client.search_zip_code, 70002900)

        mock_api_call.side_effect = TransportError("", "")
        self.assertRaises(TransportError, web_client.search_zip_code, 70002900)

    @mock.patch('openerp.addons.l10n_br_zip_correios.models.'
                'webservice_client.WebServiceClient.search_zip_code')
    def test_get_address(self, mock_api_call):

        end = 'SBN Quadra 1 Bloco A'
        bairro = 'Asa Norte'
        cidade = u'Brasília'
        uf = 'DF'
        pais = 'Brazil'

        mock_api_call.return_value = mock.MagicMock(end=end,
                                                    bairro=bairro,
                                                    cidade=cidade,
                                                    uf=uf)

        web_client = WebServiceClient(self.env['l10n_br.zip'])
        record = web_client.get_address('70002900')

        self.assertEqual(record.state_id.code, uf,
                         'Get address returns wrong UF')
        self.assertEqual(record.country_id.name, pais,
                         'Get address returns wrong country')
        self.assertEqual(record.l10n_br_city_id.name, cidade,
                         'Get address returns wrong city')
        self.assertEqual(record.street, end,
                         'Get address returns wrong address')
        self.assertEqual(record.district, bairro,
                         'Get address returns wrong neighborhood')

        mock_api_call.side_effect = UserError("")
        self.assertRaises(UserError, web_client.get_address, 70002901)

        self.assertEqual(web_client.get_address('70002900'), None,
                         'Object l10n_br.zip already created')
