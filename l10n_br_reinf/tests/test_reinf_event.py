# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_br_reinf.tools.reinf_id import EVENT_ID_LENGTH, validate_event_id

# The nfelib published on PyPI has no reinf package yet, so the round trip test
# skips itself instead of failing the suite. The import stays here, inside the
# test module, and never at the loading of the addon: a warning at load time is
# enough to turn the checklog of the CI red.
try:
    from nfelib.reinf.bindings.v2_01_02.r_1000_evt_info_contribuinte_v2_01_02 import (
        Reinf,
    )
except ImportError:  # pragma: no cover
    Reinf = None


@tagged("post_install", "-at_install")
class TestReinfEvent(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        if not cls.company.cnpj_cpf:
            cls.company.cnpj_cpf = "97.231.608/0001-69"
        cls.company.reinf_environment = "2"
        # The inscription of the event id is read from the company instead of
        # being hardcoded, so the test does not depend on which company the
        # database was built with. The alphanumeric CNPJ of the NT 03/2026 is
        # covered by the unit tests of the identifier, which do not need a
        # database.
        cls.inscription_type, cls.inscription = cls.company._reinf_inscription()
        cls.event_model = cls.env["l10n_br_reinf.event"]

    def _create_event(self, **values):
        return self.event_model.create(
            dict(
                {
                    "company_id": self.company.id,
                    "event_type": "R-4020",
                    "period": "2026-07",
                },
                **values,
            )
        )

    def test_event_key_from_sequence(self):
        """Validating an event gives it an id accepted by the layout."""
        event = self._create_event()
        self.assertFalse(event.event_key)
        event.action_validate()
        self.assertEqual(event.state, "validated")
        self.assertEqual(len(event.event_key), EVENT_ID_LENGTH)
        self.assertTrue(validate_event_id(event.event_key))
        # ID, then tpInsc, then the inscription of the taxpayer
        self.assertTrue(
            event.event_key.startswith(f"ID{self.inscription_type}{self.inscription}")
        )
        self.assertEqual(event.inscription_type, self.inscription_type)
        self.assertEqual(event.inscription, self.inscription)
        self.assertEqual(len(event.sequence), 5)

    def test_event_key_is_stable_and_unique(self):
        """The id is built once, and two events never share it."""
        first = self._create_event()
        first.action_validate()
        key = first.event_key
        first.action_set_draft()
        first.action_validate()
        self.assertEqual(first.event_key, key)

        second = self._create_event()
        second.action_validate()
        self.assertNotEqual(second.event_key, key)

    def test_event_group_is_computed(self):
        self.assertEqual(self._create_event().event_group, "periodic")
        self.assertEqual(self._create_event(event_type="R-4099").event_group, "closing")
        self.assertEqual(self._create_event(event_type="R-1000").event_group, "table")

    def test_event_refuses_invalid_period(self):
        with self.assertRaises(ValidationError):
            self._create_event(period="07/2026")

    def test_environment_is_required_to_transmit(self):
        """No silent default: an unset environment refuses the transmission."""
        self.company.reinf_environment = False
        with self.assertRaises(UserError):
            self.company._reinf_environment()

    def test_batch_refuses_closing_with_periodic(self):
        """A closing event never travels with the events it closes."""
        periodic = self._create_event()
        closing = self._create_event(event_type="R-4099")
        periodic.action_validate()
        closing.action_validate()
        with self.assertRaises(ValidationError):
            self.env["l10n_br_reinf.batch"].create(
                {
                    "company_id": self.company.id,
                    "event_ids": [(6, 0, (periodic | closing).ids)],
                }
            )

    def test_batch_send_has_no_transport_yet(self):
        """The transport is an interface: this phase ships no REST client."""
        event = self._create_event()
        event.action_validate()
        batch = self.env["l10n_br_reinf.batch"].create(
            {
                "company_id": self.company.id,
                "event_ids": [(6, 0, event.ids)],
            }
        )
        self.assertNotEqual(batch.name, "/")
        self.assertEqual(batch.event_count, 1)
        self.assertEqual(batch.event_group, "periodic")
        with self.assertRaises(NotImplementedError):
            batch.action_send()

    def test_r1000_round_trip(self):
        """A R-1000 built from the bindings serializes and parses back."""
        if Reinf is None:
            self.skipTest(
                "The installed nfelib has no reinf bindings: install a nfelib "
                "with the EFD-Reinf schemas to run the round trip."
            )
        event = self._create_event(event_type="R-1000", period="2026-07")
        event.action_validate()
        inscription_type, inscription = self.company._reinf_inscription()
        evt_class = Reinf.EvtInfoContri
        binding = Reinf(
            evtInfoContri=evt_class(
                id=event.event_key,
                ideEvento=evt_class.IdeEvento(
                    tpAmb=self.company._reinf_environment(),
                    procEmi="1",
                    verProc="Odoo l10n_br_reinf",
                ),
                ideContri=evt_class.IdeContri(
                    tpInsc=inscription_type,
                    nrInsc=inscription,
                ),
                infoContri=evt_class.InfoContri(
                    inclusao=evt_class.InfoContri.Inclusao(
                        idePeriodo=evt_class.InfoContri.Inclusao.IdePeriodo(
                            iniValid=event.period,
                        ),
                        infoCadastro=evt_class.InfoContri.Inclusao.InfoCadastro(
                            classTrib="99",
                            indEscrituracao="0",
                            indDesoneracao="0",
                            indAcordoIsenMulta="0",
                            indSitPJ="0",
                            contato=(
                                evt_class.InfoContri.Inclusao.InfoCadastro.Contato(
                                    nmCtt="Contato",
                                    cpfCtt="12345678909",
                                    foneFixo="1122223333",
                                )
                            ),
                        ),
                    ),
                ),
            ),
            # The signature is a required element of the layout, and the
            # generated binding degraded it to a plain string, so the round trip
            # carries a placeholder: the CI has no certificate, and the real
            # signature is applied on the serialized XML.
            signature="PLACEHOLDER",
        )
        xml = binding.to_xml()
        self.assertIn(event.event_key, xml)
        parsed = Reinf.from_xml(xml)
        self.assertEqual(parsed.evtInfoContri.id, event.event_key)
        self.assertEqual(parsed.signature, "PLACEHOLDER")
        self.assertEqual(parsed.evtInfoContri.ideContri.nrInsc, inscription)
        self.assertEqual(
            parsed.evtInfoContri.infoContri.inclusao.idePeriodo.iniValid,
            event.period,
        )
