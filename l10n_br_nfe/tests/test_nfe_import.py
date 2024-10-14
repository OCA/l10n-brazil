import logging

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.models import NewId
from odoo.tests import TransactionCase

_logger = logging.getLogger(__name__)


class NFeImportTest(TransactionCase):
    def test_import_in_nfe_dry_run(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )

        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())

        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding("nfe", "40", binding.NFe.infNFe, dry_run=True)
        )
        assert isinstance(nfe.id, NewId)
        self._check_nfe(nfe)

    def test_import_in_nfe(self):
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474281920007498-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())
        nfe = (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding("nfe", "40", binding.NFe.infNFe, dry_run=False)
        )

        assert isinstance(nfe.id, int)
        self._check_nfe(nfe)

    def _check_nfe(self, nfe):
        self.assertEqual(type(nfe)._name, "l10n_br_fiscal.document")

        # here we check that emit and enderEmit
        # are now the supplier data (partner_id)
        self.assertEqual(nfe.partner_id.name, "Alimentos Saudaveis")
        # (CNPJ is not formated yet in dry run)
        self.assertTrue(
            nfe.partner_id.cnpj_cpf in ("34.128.745/0001-52", "34128745000152")
        )
        # this tests the _extract_related_values method for related values:
        self.assertEqual(nfe.partner_id.legal_name, "Alimentos Ltda.")

        # enderDest
        nfe.partner_id._inverse_nfe40_CEP()
        self.assertEqual(nfe.partner_id.street_name, "Rua Fonseca")  # related xLgr
        self.assertEqual(nfe.partner_id.zip, "13877-123")
        self.assertEqual(nfe.partner_id.nfe40_CEP, "13877123")
        self.assertEqual(nfe.partner_id.city_id.name, "São João da Boa Vista")

        # now we check that company_id is unchanged
        self.assertEqual(nfe.company_id, self.env.ref("base.main_company"))

        # this tests that value is not overrident by stacked default vals
        self.assertEqual(nfe.nfe40_modFrete, "0")  # (default is 9)

        # lines data
        self.assertEqual(len(nfe.fiscal_line_ids), 6)
        self.assertEqual(nfe.fiscal_line_ids[0].quantity, 6)
        # NOTE / FIXME price unit is rounded to 7.16 if create and 7.155 if dry run
        self.assertTrue(abs(nfe.fiscal_line_ids[0].price_unit - 7.16) < 0.01)
        self.assertTrue(abs(nfe.fiscal_line_ids[0].fiscal_price - 7.16) < 0.01)

        # impostos
        self.assertEqual(nfe.fiscal_line_ids[0].icms_base_type, "0")
        self.assertEqual(nfe.fiscal_line_ids[0].icms_cst_id.code, "00")
        self.assertEqual(nfe.fiscal_line_ids[0].icms_base, 50.60)
        self.assertEqual(nfe.fiscal_line_ids[0].icms_value, 6.07)
        self.assertEqual(nfe.fiscal_line_ids[0].ipi_value, 0)

        # products
        self.assertEqual(nfe.fiscal_line_ids[0].nfe40_nItem, "1")
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.name, "QUINOA 100G (2X50G)")
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.barcode, "7897846902086")
        self.assertEqual(
            nfe.fiscal_line_ids[0].product_id.ncm_id.name[0:14], "Trigo mourisco"
        )
        self.assertEqual(nfe.fiscal_line_ids[0].product_id.ncm_id.code, "1008.50.90")

        self.assertEqual(
            nfe.fiscal_line_ids[1].product_id.name, "QUINOA VEGETAIS 100G (2X50G)"
        )
        self.assertEqual(
            nfe.fiscal_line_ids[2].product_id.name, "QUINOA PICANTE 100G (2X50G)"
        )

    def test_import_out_nfe(self):
        "(can be useful after an ERP migration)"
