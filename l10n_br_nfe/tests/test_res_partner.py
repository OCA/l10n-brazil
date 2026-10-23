# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import importlib.util
from pathlib import Path
from unittest import mock

from odoo.tests import TransactionCase


class TestNFCeResPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_id = cls.env.ref("l10n_br_base.res_partner_kmee")
        cls.partner_id.is_anonymous_consumer = True

    def test_compute_fields(self):
        self.partner_id._compute_nfe40_ender()

        self.assertFalse(self.partner_id.nfe40_xLgr)
        self.assertFalse(self.partner_id.nfe40_nro)
        self.assertFalse(self.partner_id.nfe40_xCpl)
        self.assertFalse(self.partner_id.nfe40_xBairro)
        self.assertFalse(self.partner_id.nfe40_cMun)
        self.assertFalse(self.partner_id.nfe40_xMun)
        self.assertFalse(self.partner_id.nfe40_UF)
        self.assertFalse(self.partner_id.nfe40_cPais)
        self.assertFalse(self.partner_id.nfe40_xPais)


class TestAnonymousConsumerData(TransactionCase):
    def test_anonymous_consumer_data(self):
        """The standard anonymous consumer comes marked."""
        partner = self.env.ref("l10n_br_fiscal.res_partner_anonimo")
        self.assertTrue(partner.is_anonymous_consumer)

    def test_anonymous_consumer_migration(self):
        """Databases that already have the noupdate record are fixed."""
        partner = self.env.ref("l10n_br_fiscal.res_partner_anonimo")
        partner.is_anonymous_consumer = False
        path = (
            Path(__file__).parents[1]
            / "migrations"
            / "16.0.20.0.4"
            / "post-migration.py"
        )
        spec = importlib.util.spec_from_file_location("post_migration", path)
        module = importlib.util.module_from_spec(spec)
        # openupgradelib is not required to run the tests: the decorator only
        # injects the environment, so it is replaced by an identity decorator
        fake_openupgrade = mock.Mock(migrate=lambda: lambda func: func)
        with mock.patch.dict(
            "sys.modules",
            {"openupgradelib": mock.Mock(openupgrade=fake_openupgrade)},
        ):
            spec.loader.exec_module(module)
        module.migrate(self.env, "16.0.20.0.3")
        partner.invalidate_recordset()
        self.assertTrue(partner.is_anonymous_consumer)
