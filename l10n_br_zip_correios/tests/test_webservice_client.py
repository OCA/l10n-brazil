# -*- coding: utf-8 -*-
import mock
from openerp.addons.l10n_br_zip_correios.models.webservice_client\
    import WebServiceClient

from openerp.tests.common import TransactionCase


class TestWebServiceClient(TransactionCase):

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

        record = \
            WebServiceClient(self.env['l10n_br.zip']).get_address('70002900')
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
