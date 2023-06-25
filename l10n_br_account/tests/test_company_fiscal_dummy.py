# pylint: disable=invalid-commit

from psycopg2 import IntegrityError

from odoo.tests import SavepointCase
from odoo.tools import mute_logger


class TestCompanyFiscalDummy(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Company Test",
            }
        )

    def test_if_company_have_fiscal_dummy(self):
        self.assertTrue(self.company.fiscal_dummy_id)

    def test_company_delete_fiscal_dummy(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.company.fiscal_dummy_id = None
            self.env.cr.commit()
