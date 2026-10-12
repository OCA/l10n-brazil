# Copyright 2026 Akretion - Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_base.tests.tools import load_fixture_files
from odoo.addons.l10n_br_fiscal.tests.tools import load_fiscal_fixture_files


class TestDocumentRpsNumber(TransactionCase):
    """The RPS number is the NFS-e numbering, owned by l10n_br_nfse."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        load_fiscal_fixture_files(cls.env)
        load_fixture_files(
            cls.env, "l10n_br_fiscal", file_names=["fiscal_document_nfse_demo.xml"]
        )
        cls.nfse = cls.env.ref("l10n_br_fiscal.demo_nfse_same_state")

    def test_the_document_name_falls_back_on_the_rps_number(self):
        """A NFS-e not authorized yet is named after its RPS."""
        self.assertEqual(self.nfse.rps_number, "50")
        self.assertFalse(self.nfse.document_number)
        self.assertEqual(self.nfse._get_provisional_number(), "50")
        name = self.nfse.with_context(
            fiscal_document_no_company=True
        )._compute_document_name()
        self.assertEqual(name, "SE/001/50")

    def test_the_number_assigned_from_the_serie_is_a_rps_number(self):
        self.nfse.rps_number = False
        self.nfse.document_number = False
        self.nfse._document_number_from_serie()
        self.assertTrue(self.nfse.rps_number)
        self.assertFalse(self.nfse.document_number)

    def test_the_event_number_combines_the_rps_and_the_nfse_number(self):
        self.assertEqual(self.nfse._prepare_event_document_number(), "50")
        self.nfse.document_number = "123"
        self.assertEqual(self.nfse._prepare_event_document_number(), "50-123")

    def test_the_event_number_is_the_document_number_without_a_rps(self):
        self.nfse.rps_number = False
        self.nfse.document_number = "123"
        self.assertEqual(self.nfse._prepare_event_document_number(), "123")
