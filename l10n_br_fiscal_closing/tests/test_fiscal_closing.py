# @ 2020 KMEE - www.kmee.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import os
import tempfile
import zipfile

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    EVENT_ENV_PROD,
)
from odoo.addons.l10n_br_fiscal_edi.constants.fiscal import (
    DOCUMENT_STATE_AUTHORIZED,
)


class TestFiscalClosing(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.nfe_export = cls.env.ref("l10n_br_fiscal.demo_nfe_export")
        cls.nfe_export.action_document_confirm()
        cls.closing_all = cls.env["l10n_br_fiscal.closing"].create(
            {
                "export_type": "all",
            }
        )

        cls.closing_period = cls.env["l10n_br_fiscal.closing"].create(
            {
                "export_type": "period",
                "year": str(cls.nfe_export.date_in_out.year),
                "month": str(cls.nfe_export.date_in_out.month),
            }
        )

    def test_event_to_fiscal_close(self):
        """Test Fiscal Close Export"""

        xml_file = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            '<NFe xmlns="http://www.portalfiscal.inf.br/nfe"><infNFe versao="4.00" '
            'Id="NFe26180812984794000154550010000016871192213339"><ide><cUF>26</cUF>'
            "<cNF>19221333</cNF><natOp>Venda</natOp><mod>55</mod><serie>1</serie>"
            "<nNF>1687</nNF><dhEmi>2018-08-16T16:28:18-03:00</dhEmi>"
            "<dhSaiEnt>2018-08-16T16:28:18-03:00</dhSaiEnt><tpNF>1</tpNF>"
            "<idDest>2</idDest><cMunFG>2611606</cMunFG><tpImp>1</tpImp><tpEmis>1"
            "</tpEmis><cDV>9</cDV><tpAmb>1</tpAmb><finNFe>1</finNFe><indFinal>0"
            "</indFinal><indPres>0</indPres><procEmi>0</procEmi>"
            "<verProc>Odoo Brasil v8</verProc></ide><emit>"
            "<CNPJ>75335849000115</CNPJ><xNome>Teste Produtos Médicos Ltda - ME"
            "</xNome><xFant>Teste Produtos Médicos Ltda - ME</xFant>"
            "<enderEmit><xLgr>Avenida Manoel</xLgr><nro>1</nro>"
            "<xBairro>Boa Vista</xBairro><cMun>2611606</cMun><xMun>Recife</xMun>"
            "<UF>PE</UF><CEP>50070123</CEP><cPais>1058</cPais><xPais>Brasil</xPais>"
            "<fone>0123456789</fone></enderEmit><IE>306412330</IE><CRT>3</CRT>"
            "</emit><dest><CNPJ>37148260000119</CNPJ>"
            "<xNome>MEDICOS, HOSP, IMP. E EXP. LTDA</xNome>"
            "<enderDest><xLgr>Av. Doutor Pedro</xLgr><nro>1</nro><xCpl>Sala 4</xCpl>"
            "<xBairro>Ponta da Praia</xBairro><cMun>3548500</cMun><xMun>Santos</xMun>"
            "<UF>SP</UF><CEP>11025012</CEP><cPais>1058</cPais><xPais>Brasil</xPais>"
            "<fone>99999999</fone></enderDest><indIEDest>1</indIEDest>"
            '<IE>803879214167</IE></dest><det nItem="1"><prod><cProd>880945</cProd>'
            "<cEAN>SEM GTIN</cEAN>"
            "<xProd>ESPAÇADOR TEMPORARIO DE ACRILICO PARA QUADRIL COM GENTAMICINA"
            "</xProd><NCM>90211010</NCM><CFOP>6102</CFOP><uCom>UN</uCom>"
            "<qCom>1.0000</qCom><vUnCom>2490.0000000</vUnCom><vProd>2490.00</vProd>"
            "<cEANTrib>SEM GTIN</cEANTrib><uTrib>UN</uTrib><qTrib>1.0000</qTrib>"
            "<vUnTrib>2490.0000000</vUnTrib><indTot>1</indTot></prod><imposto>"
            "<vTotTrib>0.00</vTotTrib><ICMS><ICMS40><orig>1</orig><CST>40</CST>"
            "</ICMS40></ICMS><IPI><cEnq>999</cEnq><IPINT><CST>51</CST></IPINT></IPI>"
            "<PIS><PISNT><CST>07</CST></PISNT></PIS><COFINS><COFINSNT><CST>07</CST>"
            "</COFINSNT></COFINS></imposto></det><total><ICMSTot><vBC>0.00</vBC>"
            "<vICMS>0.00</vICMS><vICMSDeson>0.00</vICMSDeson><vFCP>0.00</vFCP>"
            "<vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST>"
            "<vFCPSTRet>0.00</vFCPSTRet><vProd>2490.00</vProd><vFrete>0.00</vFrete>"
            "<vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI>"
            "<vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS>"
            "<vOutro>0.00</vOutro><vNF>2490.00</vNF><vTotTrib>0.00</vTotTrib>"
            "</ICMSTot></total><transp><modFrete>0</modFrete><vol><qVol>0</qVol>"
            "<pesoL>0.000</pesoL><pesoB>0.000</pesoB></vol></transp><pag><detPag>"
            "<tPag>99</tPag><vPag>2490.00</vPag></detPag></pag><infAdic/></infNFe>"
            '<protNFe versao="4.00"><infProt><tpAmb>1</tpAmb>'
            "<verAplic>Odoo Brasil v8</verAplic>"
            "<chNFe>26180812984794000154550010000016871192213339</chNFe>"
            "<dhRecbto>2018-08-16T16:29:21-03:00</dhRecbto>"
            "<nProt>126180026245139</nProt><digVal>XQ64+7a56OTJ7+l/eYex91y977Q=</digVal>"
            "<cStat>100</cStat><xMotivo>Autorizado o uso da NF-e</xMotivo>"
            "</infProt></protNFe></NFe></nfeProc>"
        )
        event_id = self.nfe_export.event_ids.create_event_save_xml(
            company_id=self.nfe_export.company_id,
            environment=EVENT_ENV_PROD,
            event_type="0",
            xml_file=xml_file,
            document_id=self.nfe_export,
        )
        event_id.set_done(
            status_code="101",
            response="Teste Autorizado",
            protocol_date=self.nfe_export.document_date,
            protocol_number="12345678",
            file_response_xml=xml_file,
        )
        self.nfe_export.authorization_event_id = event_id
        self.nfe_export.state_edoc = DOCUMENT_STATE_AUTHORIZED
        self.closing_all.action_export()
        self.closing_period.action_export()

        zip_file_all = base64.b64decode(self.closing_all.zip_file)
        zip_file_period = base64.b64decode(self.closing_period.zip_file)

        temp_zip_all = tempfile.NamedTemporaryFile()
        temp_zip_all.write(zip_file_all)
        temp_zip_all.seek(os.SEEK_SET)
        zip_file_all = zipfile.ZipFile(temp_zip_all.name)

        temp_zip_period = tempfile.NamedTemporaryFile()
        temp_zip_period.write(zip_file_period)
        temp_zip_period.seek(os.SEEK_SET)
        zip_file_period = zipfile.ZipFile(temp_zip_period.name)

        self.assertTrue(
            zip_file_all.namelist(), "Zip File for export all documents is empty"
        )

        self.assertTrue(
            zip_file_period.namelist(), "Zip File for period export documents is empty"
        )
