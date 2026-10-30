# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

# The nfelib published on PyPI has no reinf package yet, so the tests that need
# the bindings skip themselves instead of failing the suite. The import stays
# in the test module and never at the loading of the addon.
try:
    from nfelib.reinf.bindings.v2_01_02.r_1000_evt_info_contribuinte_v2_01_02 import (
        Reinf,
    )
except ImportError:  # pragma: no cover
    Reinf = None


@tagged("post_install", "-at_install")
class TestReinfR1000(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        if not cls.company.cnpj_cpf:
            cls.company.cnpj_cpf = "97.231.608/0001-69"
        cls.contact = cls.env["res.partner"].create(
            {
                "name": "Reinf Contact",
                "cnpj_cpf": "111.444.777-35",
                "country_id": cls.env.ref("base.br").id,
                "phone": "(11) 3881-7417",
                "email": "reinf@example.com",
            }
        )
        cls.company.write(
            {
                "reinf_environment": "2",
                "reinf_class_trib": "99",
                "reinf_ind_escrituracao": True,
                "reinf_contact_id": cls.contact.id,
            }
        )
        cls.r1000_model = cls.env["l10n_br_reinf.r1000"]

    def test_r1000_refuses_without_contact(self):
        """The R-1000 asks for a contact with a CPF, and says so."""
        self.company.reinf_contact_id = False
        with self.assertRaises(UserError):
            self.r1000_model.create_event(self.company, "2026-07")

    def test_r1000_refuses_without_class_trib(self):
        self.company.reinf_class_trib = False
        with self.assertRaises(UserError):
            self.r1000_model.create_event(self.company, "2026-07")

    def test_r1000_is_populated_from_the_company(self):
        """Everything the layout asks is copied from the company, not related."""
        event = self.r1000_model.create_event(self.company, "2026-07")
        r1000 = event.r1000_id
        inscription_type, inscription = self.company._reinf_inscription()
        self.assertEqual(event.event_type, "R-1000")
        self.assertEqual(event.state, "validated")
        self.assertEqual(r1000.reinf21_id, event.event_key)
        self.assertEqual(r1000.reinf21_tpAmb, "2")
        self.assertEqual(r1000.reinf21_tpInsc, inscription_type)
        self.assertEqual(r1000.reinf21_nrInsc, inscription)
        self.assertEqual(r1000.reinf21_iniValid, "2026-07")
        self.assertEqual(r1000.reinf21_classTrib, "99")
        self.assertEqual(r1000.reinf21_indEscrituracao, "1")
        self.assertEqual(r1000.reinf21_indDesoneracao, "0")
        self.assertEqual(r1000.reinf21_cpfCtt, "11144477735")
        self.assertEqual(r1000.reinf21_foneFixo, "1138817417")
        # The copy is deliberate: what was built must not follow the company.
        self.company.reinf_class_trib = "60"
        self.assertEqual(r1000.reinf21_classTrib, "99")

    def test_r1000_xml_is_valid_against_the_xsd(self):
        """The gate of the phase: a XML of the layout born from Odoo data."""
        if Reinf is None:
            self.skipTest(
                "The installed nfelib has no reinf bindings: install a nfelib "
                "with the EFD-Reinf schemas to validate the XML."
            )
        event = self.r1000_model.create_event(self.company, "2026-07")
        xml = event._serialize()

        # No error at all in the payload.
        self.assertEqual(event._xsd_errors(xml), [])
        # And the only thing missing is the signature, which the transmission
        # applies and which the layout does require.
        full_errors = event._xsd_errors(xml, ignore_signature=False)
        self.assertEqual(len(full_errors), 1)
        self.assertIn("Signature", full_errors[0])

        self.assertIn(f'id="{event.event_key}"', xml)
        self.assertIn("<inclusao>", xml)
        # Only one branch of the choice of infoContri is serialized.
        self.assertNotIn("<alteracao>", xml)
        self.assertNotIn("<exclusao>", xml)

        event.action_generate_xml()
        self.assertTrue(event.file_request_id)
        self.assertEqual(event.file_request_id.name, f"{event.event_key}-env.xml")

    def test_generate_xml_refuses_an_invalid_event(self):
        """A XML that does not match the layout raises a message, not a
        traceback."""
        if Reinf is None:
            self.skipTest("The installed nfelib has no reinf bindings.")
        event = self.r1000_model.create_event(self.company, "2026-07")
        # classTrib takes 2 digits, so this one is refused by the XSD.
        event.r1000_id.reinf21_classTrib = "XX"
        with self.assertRaises(UserError):
            event.action_generate_xml()
        self.assertFalse(event.file_request_id)


@tagged("post_install", "-at_install")
class TestReinfNatureIncome(TransactionCase):
    def test_flags_are_read_from_the_mapping(self):
        """The withholding flags of a nature come from the Annex I mapping."""
        nature = self.env["l10n_br_reinf.nature.income"].create(
            {"code": "99999", "name": "Nature of a test"}
        )
        self.assertFalse(nature.ret_ir)
        self.assertFalse(nature.ret_agreg)

        self.env["l10n_br_reinf.nature.income.tax"].create(
            {
                "nature_income_id": nature.id,
                "event_type": "R-4020",
                "tax_type": "aggregated",
                "revenue_code": "595207",
                "periodicity": "monthly",
            }
        )
        self.assertTrue(nature.ret_agreg)
        self.assertFalse(nature.ret_ir)

        self.env["l10n_br_reinf.nature.income.tax"].create(
            {
                "nature_income_id": nature.id,
                "event_type": "R-4020",
                "tax_type": "irpj",
                "revenue_code": "170806",
                "periodicity": "monthly",
            }
        )
        self.assertTrue(nature.ret_ir)

    def test_annex_data_is_loaded(self):
        """The Annex I of the manual is in the database, not in a spreadsheet."""
        natures = self.env["l10n_br_reinf.nature.income"].search([])
        self.assertGreaterEqual(len(natures), 215)
        aluguel = self.env.ref("l10n_br_reinf.nature_income_13002")
        self.assertTrue(aluguel.ret_ir)
        self.assertTrue(aluguel.tax_ids)
