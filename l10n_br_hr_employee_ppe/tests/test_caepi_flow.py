# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from unittest.mock import patch

from odoo.tests.common import Form, TransactionCase

from odoo.addons.l10n_br_hr_employee_ppe.lib.client import CAEPIError

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

    def test_product_compute_no_certification(self):
        product = self.Product.create(
            {
                "name": "Produto sem CA",
                "is_ppe": True,
                "is_personal_equipment": True,
            }
        )
        self.assertFalse(product.caepi_situacao)
        self.assertFalse(product.caepi_equipamento)
        self.assertFalse(product.caepi_fabricante)

    def test_product_compute_cert_not_in_db(self):
        product = self.Product.create(
            {
                "name": "CA inexistente",
                "is_ppe": True,
                "is_personal_equipment": True,
                "ppe_certification": "00000",
            }
        )
        self.assertFalse(product.caepi_situacao)

    def test_onchange_cert_not_found_warns(self):
        self._run_sync()
        product_form = Form(
            self.Product.with_context(default_is_ppe=True),
        )
        product_form.name = "Teste onchange"
        product_form.is_personal_equipment = True
        product_form.ppe_certification = "88888"
        product = product_form.save()
        self.assertFalse(product.ppe_certification_expiry_date)

    def test_onchange_valid_cert_sets_date(self):
        self._run_sync()
        product_form = Form(
            self.Product.with_context(default_is_ppe=True),
        )
        product_form.name = "Botina onchange"
        product_form.is_personal_equipment = True
        product_form.ppe_certification = "42016"
        product = product_form.save()
        self.assertEqual(product.ppe_certification_expiry_date, date(2027, 12, 30))

    def test_onchange_cancelled_cert_sets_date(self):
        self._run_sync()
        product_form = Form(
            self.Product.with_context(default_is_ppe=True),
        )
        product_form.name = "Luva cancelada"
        product_form.is_personal_equipment = True
        product_form.ppe_certification = "99999"
        product = product_form.save()
        self.assertFalse(product.ppe_certification_expiry_date)

    def test_onchange_empty_certification(self):
        product_form = Form(
            self.Product.with_context(default_is_ppe=True),
        )
        product_form.name = "Sem CA"
        product_form.is_personal_equipment = True
        product_form.ppe_certification = ""
        product = product_form.save()
        self.assertFalse(product.ppe_certification_expiry_date)

    def test_lookup_empty_string(self):
        result = self.Cert.lookup("")
        self.assertFalse(result)

    def test_lookup_zero(self):
        result = self.Cert.lookup("0")
        self.assertFalse(result)

    def test_cron_handles_download_error(self):
        with patch(
            "odoo.addons.l10n_br_hr_employee_ppe.models."
            "caepi_certificate.download_and_parse",
            side_effect=CAEPIError("Connection refused"),
        ):
            self.Cert._cron_refresh()
        self.assertFalse(self.Cert.search([]))

    def test_cron_handles_empty_rows(self):
        with patch(
            "odoo.addons.l10n_br_hr_employee_ppe.models."
            "caepi_certificate.download_and_parse",
            return_value=[],
        ):
            self.Cert._cron_refresh()
        self.assertFalse(self.Cert.search([]))

    def test_get_ftp_url_from_param(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_br_hr_employee_ppe.caepi_ftp_url",
            "ftp://custom.server/caepi.zip",
        )
        url = self.Cert._get_ftp_url()
        self.assertEqual(url, "ftp://custom.server/caepi.zip")

    def test_action_manual_refresh(self):
        with patch(
            "odoo.addons.l10n_br_hr_employee_ppe.models."
            "caepi_certificate.download_and_parse",
            return_value=FAKE_ROWS,
        ):
            result = self.Cert.action_manual_refresh()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertTrue(self.Cert.search([("numero_ca", "=", "42016")]))

    def test_update_product_dates_no_change(self):
        self._run_sync()
        product = self.Product.create(
            {
                "name": "Botina sync",
                "is_ppe": True,
                "is_personal_equipment": True,
                "ppe_certification": "42016",
                "ppe_certification_expiry_date": date(2027, 12, 30),
            }
        )
        self.Cert._update_product_dates()
        product.invalidate_recordset()
        self.assertEqual(product.ppe_certification_expiry_date, date(2027, 12, 30))

    def test_update_product_dates_cert_not_found(self):
        product = self.Product.create(
            {
                "name": "CA fantasma",
                "is_ppe": True,
                "is_personal_equipment": True,
                "ppe_certification": "00001",
            }
        )
        self.Cert._update_product_dates()
        product.invalidate_recordset()
        self.assertFalse(product.ppe_certification_expiry_date)
