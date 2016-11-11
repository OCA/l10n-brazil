import mock

from openerp.tests.common import TransactionCase

class classeTeste:
    def __init__(self, uf, country_id, cidade, end, bairro, complemento):
        self.uf = uf
        self.country_id = country_id
        self.cidade = cidade
        self.end = end
        self.bairro = bairro
        self.complemento = complemento

class TestGetAdress(TransactionCase, classeTeste):
    @mock.patch('webservice.client.suds.consulta.servece.consultaCep')
    def test_get_adress(self, mock_api_call):
        mock_api_call.return_value = classeTeste("SP", "Brazil", "Votuporanga", "Rua Antonio Cramolichi", "São João", "")

        record = self.get_address('15501-198')
        assert record.uf == u'SP', 'Get address returns wrong UF'
        assert record.country_id == u'Brazil', 'Get address returns wrong country'
        assert record.cidade == u'Votuporanga', 'Get address returns wrong city'
        assert record.end == u'Rua Antonio Cramolichi', 'Get address returns wrong address'
        assert record.bairro == u'São João', 'Get address returns wrong neighborhood'
        assert record.complemento == u'', 'Get address returns wrong complement'
