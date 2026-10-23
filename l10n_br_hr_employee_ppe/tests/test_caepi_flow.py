# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase

FAKE_ROWS = [
    {
        "numero_ca": "42016",
        "situacao": "valid",
        "data_validade": date(2027, 12, 30),
        "equipamento": "BOTINA - TIPO B",
        "fabricante": "BSB PRODUTORA",
        "cnpj_fabricante": "11222333000144",
        "natureza": "Nacional",
        "norma": "NBR 12345",
        "aprovado_para": "PROTEÇÃO DOS PÉS",
    },
    {
        "numero_ca": "31469",
        "situacao": "valid",
        "data_validade": date(2028, 5, 23),
        "equipamento": "CAPACETE CLASSE E",
        "fabricante": "PLASTCOR",
        "cnpj_fabricante": "55666777000188",
        "natureza": "Nacional",
        "norma": "NBR 99999",
        "aprovado_para": "PROTEÇÃO DA CABEÇA",
    },
    {
        "numero_ca": "99999",
        "situacao": "cancelled",
        "data_validade": None,
        "equipamento": "LUVA",
        "fabricante": "TESTE",
        "cnpj_fabricante": "00000000000100",
        "natureza": "Nacional",
        "norma": "",
        "aprovado_para": "",
    },
]


class TestCAEPIFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env["product.template"]
        cls.Cert = cls.env["caepi.certificate"]

    def _run_sync(self):
        with patch(
            "odoo.addons.l10n_br_hr_employee_ppe.models."
            "caepi_certificate.download_and_parse",
            return_value=FAKE_ROWS,
        ):
            self.Cert._cron_refresh()

    def test_cron_creates_certificates(self):
        self._run_sync()
        cert = self.Cert.lookup("42016")
        self.assertTrue(cert)
        self.assertEqual(cert.situacao, "valid")
        self.assertEqual(cert.data_validade, date(2027, 12, 30))
        self.assertEqual(cert.fabricante, "BSB PRODUTORA")

    def test_cron_upserts_on_rerun(self):
        self._run_sync()
        cert = self.Cert.lookup("42016")
        first_sync = cert.last_sync

        self._run_sync()
        cert.invalidate_recordset()
        self.assertTrue(cert.last_sync >= first_sync)

    def test_cron_updates_product_dates(self):
        product = self.Product.create(
            {
                "name": "Botina teste",
                "is_ppe": True,
                "is_personal_equipment": True,
                "ppe_certification": "42016",
            }
        )
        self.assertFalse(product.ppe_certification_expiry_date)

        self._run_sync()
        product.invalidate_recordset()
        self.assertEqual(product.ppe_certification_expiry_date, date(2027, 12, 30))

    def test_lookup_normalizes(self):
        self._run_sync()
        self.assertTrue(self.Cert.lookup("42.016"))
        self.assertTrue(self.Cert.lookup("CA-42016"))
        self.assertTrue(self.Cert.lookup("042016"))

    def test_lookup_not_found(self):
        self._run_sync()
        self.assertFalse(self.Cert.lookup("00000"))

    def test_product_compute_caepi_info(self):
        self._run_sync()
        product = self.Product.create(
            {
                "name": "Luva teste",
                "is_ppe": True,
                "is_personal_equipment": True,
                "ppe_certification": "99999",
            }
        )
        self.assertEqual(product.caepi_situacao, "Cancelled")
        self.assertEqual(product.caepi_equipamento, "LUVA")
        self.assertEqual(product.caepi_fabricante, "TESTE")
