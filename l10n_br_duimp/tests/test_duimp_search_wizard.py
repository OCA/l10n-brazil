# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_account.tests.common import AccountMoveBRCommon
from odoo.addons.l10n_br_duimp.models.res_company import ResCompany

from .test_duimp_import_wizard import FakeDuimpWebservice


class FakeDuimpSearchWebservice(FakeDuimpWebservice):
    """Extends FakeDuimpWebservice with the access-key listing used by
    the search wizard, still never touching the network."""

    def __init__(self, access_keys=None, **kwargs):
        super().__init__(**kwargs)
        self.access_keys = access_keys if access_keys is not None else []

    def search_access_keys_by_importer(
        self, importer_ni, date_from, date_to, offset=0, limit=100
    ):
        return self.access_keys


@tagged("post_install", "-at_install")
class TestDuimpSearchWizard(AccountMoveBRCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref or "l10n_br_coa.l10n_br_coa_template")
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.company_data["company"]
        cls.company.cnpj_cpf = "42.245.642/0001-09"

    def _create_wizard(self):
        return self.env["l10n_br_duimp.search_wizard"].create(
            {"company_id": self.company.id}
        )

    def test_action_search_duimp_lists_and_excludes_imported(self):
        self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "issuer": "company",
                "duimp_number": "26BR0000758808",
            }
        )
        fake = FakeDuimpSearchWebservice(
            access_keys=[
                {"numero": "26BR0000758808", "chaveAcesso": "already-imported"},
                {"numero": "26BR0000999999", "chaveAcesso": "new"},
            ]
        )
        wizard = self._create_wizard()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            wizard.action_search_duimp()

        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.duimp_number, "26BR0000999999")
        self.assertEqual(wizard.line_ids.duimp_version, 1)

    def test_action_search_duimp_ignores_entries_without_number(self):
        fake = FakeDuimpSearchWebservice(access_keys=[{"chaveAcesso": "no-numero"}])
        wizard = self._create_wizard()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            with self.assertRaises(UserError):
                wizard.action_search_duimp()
        self.assertFalse(wizard.line_ids)

    def test_action_search_duimp_raises_when_no_results(self):
        fake = FakeDuimpSearchWebservice(access_keys=[])
        wizard = self._create_wizard()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            with self.assertRaises(UserError):
                wizard.action_search_duimp()

    def test_action_search_duimp_raises_when_all_already_imported(self):
        self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
                "issuer": "company",
                "duimp_number": "26BR0000758808",
            }
        )
        fake = FakeDuimpSearchWebservice(
            access_keys=[{"numero": "26BR0000758808", "chaveAcesso": "x"}]
        )
        wizard = self._create_wizard()
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            with self.assertRaises(UserError):
                wizard.action_search_duimp()

    def test_action_search_duimp_requires_cnpj(self):
        wizard = self._create_wizard()
        self.company.cnpj_cpf = False
        with self.assertRaises(UserError):
            wizard.action_search_duimp()

    def test_action_import_selected_requires_selection(self):
        wizard = self._create_wizard()
        wizard.line_ids = [
            (0, 0, {"duimp_number": "26BR0000999999", "selected": False})
        ]
        with self.assertRaises(UserError):
            wizard.action_import_selected()

    def test_action_import_selected_creates_import_wizards(self):
        fake = FakeDuimpSearchWebservice()
        wizard = self._create_wizard()
        wizard.line_ids = [
            (
                0,
                0,
                {
                    "duimp_number": "26BR0000758808",
                    "duimp_version": 1,
                    "selected": True,
                },
            )
        ]
        with patch.object(ResCompany, "_get_duimp_webservice", new=lambda self: fake):
            action = wizard.action_import_selected()

        import_wizards = self.env["l10n_br_fiscal.document.import.wizard"].search(
            [("id", "in", action["domain"][0][2])]
        )
        self.assertEqual(len(import_wizards), 1)
        self.assertEqual(import_wizards.duimp_number, "26BR0000758808")
        self.assertTrue(import_wizards.duimp_line_ids)
