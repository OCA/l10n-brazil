# Copyright 2020 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64

from odoo.tests.common import TransactionCase
from datetime import datetime


class TestFiscalDocumentNFSe(TransactionCase):

    def setUp(self):
        super(TestFiscalDocumentNFSe, self).setUp()
        # Contribuinte
        self.nfse_same_state = self.env.ref(
            'l10n_br_nfse.demo_nfse_same_state'
        ).copy()

    def test_nfse_same_state(self):
        """ Test NFS-e same state. """

        self.nfse_same_state._onchange_document_serie_id()
        self.nfse_same_state._onchange_partner_id()
        self.nfse_same_state._onchange_fiscal_operation_id()
        self.nfse_same_state.rps_number = 50
        self.nfse_same_state.date = datetime.strptime(
            '2020-06-04T11:58:46', '%Y-%m-%dT%H:%M:%S')

        for line in self.nfse_same_state.line_ids:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        self.nfse_same_state.action_document_confirm()

        self.assertEqual(
            base64.b64decode(self.nfse_same_state.file_xml_id.datas
                             ).decode('utf-8'),
            '<EnviarLoteRpsEnvio xmlns="http://www.ginfes.com.br/'
            'servico_enviar_lote_rps_envio_v03.xsd" xmlns:tipos="http://'
            'www.ginfes.com.br/tipos_v03.xsd"><LoteRps><tipos:Cnpj>'
            '23130935000198</tipos:Cnpj><tipos:InscricaoMunicipal>35172'
            '</tipos:InscricaoMunicipal><tipos:QuantidadeRps>1</tipos:'
            'QuantidadeRps><ListaRps xmlns="http://www.ginfes.com.br/'
            'tipos_v03.xsd"><Rps><InfRps Id="rps50"><IdentificacaoRps>'
            '<Numero>50</Numero><Serie>001</Serie><Tipo>1</Tipo>'
            '</IdentificacaoRps><DataEmissao>2020-06-04T13:58:46'
            '</DataEmissao><NaturezaOperacao>1</NaturezaOperacao>'
            '<RegimeEspecialTributacao>1</RegimeEspecialTributacao>'
            '<OptanteSimplesNacional>1</OptanteSimplesNacional>'
            '<IncentivadorCultural>2</IncentivadorCultural><Status>1</Status>'
            '<Servico><Valores><ValorServicos>100.</ValorServicos>'
            '<ValorDeducoes>0.</ValorDeducoes><ValorPis>0.</ValorPis>'
            '<ValorCofins>0.</ValorCofins><ValorInss>0.</ValorInss><ValorIr>'
            '0.</ValorIr><ValorCsll>0.</ValorCsll><IssRetido>2</IssRetido>'
            '<ValorIss>2.</ValorIss><ValorIssRetido>0.</ValorIssRetido>'
            '<OutrasRetencoes>0.</OutrasRetencoes><BaseCalculo>100.'
            '</BaseCalculo><Aliquota>0.02</Aliquota><ValorLiquidoNfse>100.'
            '</ValorLiquidoNfse></Valores><ItemListaServico>105'
            '</ItemListaServico><CodigoTributacaoMunicipio>6202300'
            '</CodigoTributacaoMunicipio><Discriminacao>[ODOO_DEV] Customized'
            ' Odoo Development</Discriminacao><CodigoMunicipio>3132404'
            '</CodigoMunicipio></Servico><Prestador><tipos:Cnpj>'
            '23130935000198</tipos:Cnpj><tipos:InscricaoMunicipal>35172'
            '</tipos:InscricaoMunicipal></Prestador><Tomador>'
            '<IdentificacaoTomador><CpfCnpj><Cnpj>81493979000189</Cnpj>'
            '</CpfCnpj></IdentificacaoTomador><RazaoSocial>Cliente 1 SP'
            '</RazaoSocial><Endereco><Endereco>Rua Samuel Morse</Endereco>'
            '<Numero>135</Numero><Bairro>Brooklin</Bairro><CodigoMunicipio>'
            '3550308</CodigoMunicipio><Uf>SP</Uf><Cep>4576060</Cep>'
            '</Endereco></Tomador></InfRps></Rps></ListaRps></LoteRps>'
            '</EnviarLoteRpsEnvio>',
            "Erro na serialização!"
        )
