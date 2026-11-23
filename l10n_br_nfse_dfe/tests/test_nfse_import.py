# Copyright 2026 Escodoo - Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_PARTNER,
    MODELO_FISCAL_NFSE,
)
from odoo.addons.l10n_br_nfse.services.nfse_xml import parse_nfse_xml
from odoo.addons.l10n_br_nfse_dfe.tests.test_nfse_dfe import (
    ACCESS_KEY,
    PROVIDER_CNPJ,
    TAKER_CNPJ,
    nfse_xml,
)


class TestNfseImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.provider = cls.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", PROVIDER_CNPJ)], limit=1
        )
        if not cls.provider:
            raise AssertionError("Demo provider CNPJ 59594315000157 was not found")
        service_model = cls.env["l10n_br_fiscal.service.type"]
        cls.service_type = service_model.search([("code", "=", "1.01.01")], limit=1)
        if not cls.service_type:
            cls.service_type = service_model.create(
                {
                    "code": "1.01.01",
                    "name": "Test national service",
                    "internal_type": "normal",
                }
            )
        nbs_model = cls.env["l10n_br_fiscal.nbs"]
        cls.nbs = nbs_model.search([("code_unmasked", "=", "123456789")], limit=1)
        if not cls.nbs:
            cls.nbs = nbs_model.create(
                {
                    "code": "123456789",
                    "name": "Test NBS",
                    "code_unmasked": "123456789",
                }
            )

    def _import(self, content):
        """Import the file with the generic service and return its document."""
        # the company is the taker of the file, so every company is allowed
        documents, errors, warnings = (
            self.env["l10n_br_fiscal.document"]
            .with_context(allowed_company_ids=self.env["res.company"].search([]).ids)
            .with_company(self.company)
            ._edi_import_files([("nfse.xml", content)])
        )
        self.assertFalse(errors)
        self._warnings = warnings
        return documents

    def test_import_creates_inbound_service_document_once(self):
        document = self._import(nfse_xml(retention="1"))
        self.assertEqual(document.document_type_id.code, MODELO_FISCAL_NFSE)
        self.assertEqual(document.issuer, DOCUMENT_ISSUER_PARTNER)
        self.assertTrue(document.imported_document)
        self.assertEqual(document.fiscal_operation_type, "in")
        self.assertEqual(document.document_key, ACCESS_KEY)
        self.assertEqual(document.document_serie, "00007")
        self.assertEqual(document.partner_id, self.provider)
        line = document.fiscal_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.name, "Consulting")
        self.assertAlmostEqual(line.price_unit, 20.0)
        self.assertAlmostEqual(line.issqn_value, 0.4)
        self.assertEqual(line.issqn_tax_id, self.env.ref("l10n_br_fiscal.tax_issqn_2"))
        self.assertIn(line.issqn_tax_id, line.fiscal_tax_ids)
        self.assertFalse(line.issqn_wh_tax_id)
        self.assertEqual(line.issqn_fg_city_id.ibge_code, "3550308")
        self.assertEqual(line.service_type_id, self.service_type)
        self.assertEqual(line.nbs_id, self.nbs)
        self.assertAlmostEqual(line.issqn_wh_value, 0.0)

        again = self._import(nfse_xml(retention="1"))
        self.assertEqual(again, document)
        self.assertEqual(len(self._warnings), 1)
        self.assertEqual(
            self.env["l10n_br_fiscal.document"].search_count(
                [("document_key", "=", ACCESS_KEY)]
            ),
            1,
        )

    def test_retention_codes_two_and_three_withhold_issqn(self):
        withheld = parse_nfse_xml(nfse_xml(retention="2"))
        self.assertEqual(withheld["provider_cnpj"], PROVIDER_CNPJ)
        self.assertEqual(withheld["issqn_wh_value"], 0.4)
        not_withheld = parse_nfse_xml(nfse_xml(retention="1"))
        self.assertEqual(not_withheld["issqn_wh_value"], 0.0)
        document = self._import(nfse_xml(retention="2"))
        line = document.fiscal_line_ids
        self.assertEqual(line.issqn_tax_id, self.env.ref("l10n_br_fiscal.tax_issqn_2"))
        self.assertEqual(
            line.issqn_wh_tax_id, self.env.ref("l10n_br_fiscal.tax_issqn_wh_2")
        )
        self.assertIn(line.issqn_wh_tax_id, line.fiscal_tax_ids)

    def test_import_keeps_ibs_cbs_and_federal_withholdings(self):
        parsed = parse_nfse_xml(_reform_nfse_xml())
        self.assertEqual(parsed["ibs_base"], 3575.44)
        self.assertEqual(parsed["ibs_percent"], 0.10)
        self.assertEqual(parsed["ibs_reduction"], 30.0)
        self.assertEqual(parsed["ibs_value"], 2.50)
        self.assertEqual(parsed["cbs_percent"], 0.90)
        self.assertEqual(parsed["cbs_reduction"], 30.0)
        self.assertEqual(parsed["cbs_value"], 22.53)
        self.assertEqual(parsed["ibs_cbs_cst"], "200")
        self.assertEqual(parsed["tax_classification_code"], "200052")
        self.assertEqual(parsed["pis_value"], 25.44)
        self.assertEqual(parsed["cofins_value"], 117.42)
        self.assertTrue(parsed["pis_withheld"])
        self.assertTrue(parsed["cofins_withheld"])
        self.assertEqual(parsed["irpj_wh_value"], 58.71)
        self.assertEqual(parsed["csll_wh_value"], 39.14)
        self.assertEqual(parsed["issqn_wh_value"], 0.0)
        self.assertEqual(parsed["issqn_city_ibge"], "3205200")

        document = self._import(_reform_nfse_xml())
        line = document.fiscal_line_ids
        self.assertAlmostEqual(line.price_unit, 3914.0)
        self.assertAlmostEqual(line.issqn_value, 195.70)
        self.assertEqual(line.issqn_tax_id, self.env.ref("l10n_br_fiscal.tax_issqn_5"))
        self.assertIn(line.issqn_tax_id, line.fiscal_tax_ids)
        self.assertFalse(line.issqn_wh_tax_id)
        self.assertEqual(line.issqn_fg_city_id.ibge_code, "3205200")
        self.assertAlmostEqual(line.ibs_base, 3575.44)
        self.assertAlmostEqual(line.ibs_percent, 0.10)
        self.assertAlmostEqual(line.ibs_reduction, 30.0)
        self.assertAlmostEqual(line.ibs_value, 2.50)
        self.assertAlmostEqual(line.cbs_percent, 0.90)
        self.assertAlmostEqual(line.cbs_reduction, 30.0)
        self.assertAlmostEqual(line.cbs_value, 22.53)
        self.assertEqual(line.ibs_cst_id.code, "200")
        self.assertEqual(line.cbs_cst_id.code, "200")
        self.assertEqual(line.tax_classification_id.code, "200052")
        self.assertEqual(line.ibs_tax_id, line.tax_classification_id.tax_ibs_id)
        self.assertEqual(line.cbs_tax_id, line.tax_classification_id.tax_cbs_id)
        self.assertAlmostEqual(line.pis_value, 25.44)
        self.assertAlmostEqual(line.pis_wh_value, 25.44)
        self.assertAlmostEqual(line.cofins_value, 117.42)
        self.assertAlmostEqual(line.cofins_wh_value, 117.42)
        self.assertEqual(line.pis_cst_id.code, "01")
        self.assertEqual(line.cofins_cst_id.code, "01")
        self.assertAlmostEqual(line.irpj_wh_value, 58.71)
        self.assertAlmostEqual(line.irpj_wh_percent, 1.5)
        self.assertAlmostEqual(line.csll_wh_value, 39.14)
        self.assertIn(line.ibs_tax_id, line.fiscal_tax_ids)
        self.assertIn(line.cbs_tax_id, line.fiscal_tax_ids)
        self.assertIn(line.pis_tax_id, line.fiscal_tax_ids)
        self.assertIn(line.cofins_tax_id, line.fiscal_tax_ids)

    def test_import_reads_the_nt009_ibs_cbs_classification(self):
        """NT 009 moved CST and cClassTrib out of the gIBSCBS group."""
        parsed = parse_nfse_xml(_reform_nfse_xml(nt009_layout=True))
        self.assertEqual(parsed["ibs_cbs_cst"], "200")
        self.assertEqual(parsed["tax_classification_code"], "200052")
        self.assertEqual(parsed["ibs_value"], 2.50)
        self.assertEqual(parsed["cbs_value"], 22.53)
        self.assertEqual(parsed["pis_value"], 25.44)

    def test_import_creates_unknown_provider(self):
        cnpj = "12345678000195"
        self.assertFalse(
            self.env["res.partner"].search([("cnpj_cpf_stripped", "=", cnpj)], limit=1)
        )
        key = "1" * 50
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe Id="NFS{key}">
    <nNFSe>9</nNFSe>
    <dhProc>2023-09-09T12:42:06-03:00</dhProc>
    <cLocIncid>3550308</cLocIncid>
    <emit>
      <CNPJ>{cnpj}</CNPJ>
      <xNome>Created Provider LTDA</xNome>
      <xFant>Created Provider</xFant>
    </emit>
    <valores><vLiq>20.00</vLiq></valores>
    <DPS><infDPS>
      <serie>1</serie><nDPS>9</nDPS>
      <prest>
        <CNPJ>{cnpj}</CNPJ>
        <IM>12345</IM>
        <fone>1133334444</fone>
        <email>provider@example.com</email>
        <end>
          <endNac><cMun>3550308</cMun><CEP>01310100</CEP></endNac>
          <xLgr>Paulista</xLgr>
          <nro>1000</nro>
          <xBairro>Bela Vista</xBairro>
        </end>
      </prest>
      <toma><CNPJ>{self.company.partner_id.cnpj_cpf_stripped}</CNPJ></toma>
      <serv><cServ><xDescServ>Consulting</xDescServ></cServ></serv>
      <valores><vServPrest><vServ>20.00</vServ></vServPrest></valores>
    </infDPS></DPS>
  </infNFSe>
</NFSe>
""".encode()
        document = self._import(xml)
        partner = self.env["res.partner"].search(
            [("cnpj_cpf_stripped", "=", cnpj)], limit=1
        )
        self.assertEqual(document.partner_id, partner)
        self.assertEqual(partner.legal_name, "Created Provider LTDA")
        self.assertEqual(partner.name, "Created Provider")
        self.assertEqual(partner.cnpj_cpf_stripped, cnpj)
        self.assertTrue(partner.is_company)
        self.assertEqual(partner.l10n_br_im_code, "12345")
        self.assertEqual(partner.street_name, "Paulista")
        self.assertEqual(partner.street_number, "1000")
        self.assertEqual(partner.district, "Bela Vista")
        self.assertEqual(partner.zip, "01310100")
        self.assertEqual(partner.city_id.ibge_code, "3550308")
        self.assertEqual(partner.country_id.code, "BR")
        self.assertEqual(partner.phone, "1133334444")
        self.assertEqual(partner.email, "provider@example.com")


def _reform_nfse_xml(nt009_layout=False):
    """Minimal national NFS-e with the IBS/CBS layout of a real inbound note.

    ``nt009_layout`` writes CST and cClassTrib under ``valores/trib``, where
    leiaute 1.04.01 (NT 009) puts them. The default keeps them inside the
    ``gIBSCBS`` group of the previous layout, as notes already authorized do.
    """
    key = "3" * 50
    classification = (
        "<valores><trib><CST>200</CST><cClassTrib>200052</cClassTrib>"
        "<gIBSCBS><cCredPres>01</cCredPres></gIBSCBS></trib></valores>"
        if nt009_layout
        else "<valores><trib><gIBSCBS><CST>200</CST>"
        "<cClassTrib>200052</cClassTrib></gIBSCBS></trib></valores>"
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe Id="NFS{key}">
    <nNFSe>313</nNFSe>
    <cLocIncid>3205200</cLocIncid>
    <dhProc>2026-10-02T00:00:00-03:00</dhProc>
    <emit><CNPJ>31372555000198</CNPJ><xNome>Provider</xNome></emit>
    <valores>
      <vBC>3914.00</vBC>
      <pAliqAplic>5.00</pAliqAplic>
      <vISSQN>195.70</vISSQN>
      <vTotalRet>240.71</vTotalRet>
      <vLiq>3673.29</vLiq>
    </valores>
    <IBSCBS>
      <valores>
        <vBC>3575.44</vBC>
        <uf>
          <pIBSUF>0.10</pIBSUF>
          <pRedAliqUF>30.00</pRedAliqUF>
          <pAliqEfetUF>0.07</pAliqEfetUF>
        </uf>
        <mun>
          <pIBSMun>0.00</pIBSMun>
          <pRedAliqMun>30.00</pRedAliqMun>
          <pAliqEfetMun>0.00</pAliqEfetMun>
        </mun>
        <fed>
          <pCBS>0.90</pCBS>
          <pRedAliqCBS>30.00</pRedAliqCBS>
          <pAliqEfetCBS>0.63</pAliqEfetCBS>
        </fed>
      </valores>
      <totCIBS>
        <gIBS>
          <vIBSTot>2.50</vIBSTot>
          <gIBSUFTot><vIBSUF>2.50</vIBSUF></gIBSUFTot>
          <gIBSMunTot><vIBSMun>0.00</vIBSMun></gIBSMunTot>
        </gIBS>
        <gCBS><vCBS>22.53</vCBS></gCBS>
      </totCIBS>
    </IBSCBS>
    <DPS>
      <infDPS>
        <dhEmi>2026-10-02T00:00:00-03:00</dhEmi>
        <serie>49999</serie>
        <nDPS>313</nDPS>
        <prest><CNPJ>{PROVIDER_CNPJ}</CNPJ><xNome>Provider Test</xNome></prest>
        <toma><CNPJ>{TAKER_CNPJ}</CNPJ><xNome>Taker</xNome></toma>
        <serv><cServ>
          <cTribNac>070101</cTribNac>
          <xDescServ>Engineering</xDescServ>
          <cNBS>114039000</cNBS>
        </cServ></serv>
        <valores>
          <vServPrest><vServ>3914.00</vServ></vServPrest>
          <trib>
            <tribMun><tribISSQN>1</tribISSQN><tpRetISSQN>1</tpRetISSQN></tribMun>
            <tribFed>
              <piscofins>
                <CST>01</CST>
                <vBCPisCofins>3914.00</vBCPisCofins>
                <pAliqPis>0.65</pAliqPis>
                <pAliqCofins>3.00</pAliqCofins>
                <vPis>25.44</vPis>
                <vCofins>117.42</vCofins>
                <tpRetPisCofins>3</tpRetPisCofins>
              </piscofins>
              <vRetIRRF>58.71</vRetIRRF>
              <vRetCSLL>182.00</vRetCSLL>
            </tribFed>
          </trib>
        </valores>
        <IBSCBS>
          {classification}
        </IBSCBS>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
""".encode()
