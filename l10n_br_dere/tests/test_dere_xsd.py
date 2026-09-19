# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_br_dere_spec.models import xsd_validator

from .common import DereCommon
from .test_dere_transmit import _FakeResponse


@tagged("post_install", "-at_install")
class TestDereXsd(DereCommon):
    def _validate_generated(self, declaration, event_types):
        for event_type in event_types:
            event = declaration.event_ids.filtered(
                lambda ev, current=event_type: ev.event_type == current
            ).sorted("id")[-1:]
            self.assertTrue(event.xml_content, event_type)
            self.assertFalse(
                xsd_validator.validate(event.xml_content, event_type),
                event_type,
            )

    def test_generated_events_match_official_xsd(self):
        self.company.dere_subject_d1106 = True
        self.company.dere_subject_d1121 = True
        declaration = self._create_declaration()
        declaration.action_generate_tables()
        self._post_billing_split("2026-10-15", 12500.0, 1000.0)
        declaration.action_generate_d1101()
        declaration.action_generate_d1106()
        declaration.action_generate_d1199()
        self._accept_closing(declaration)
        declaration.action_mark_reopened()
        self._validate_generated(
            declaration,
            ("D-1001", "D-1011", "D-1101", "D-1106", "D-1199", "D-1198"),
        )

    def test_send_validates_signed_event_and_lote(self):
        declaration = self._create_declaration("2026-09")
        declaration.action_generate_d1001()

        def fake_post(url, **_kwargs):
            if "token" in url:
                return _FakeResponse(
                    payload={"access_token": "tok", "expires_in": 3600}
                )
            return _FakeResponse(
                text='{"protocolo": "PROT-2026-0000000001"}',
                payload={"protocolo": "PROT-2026-0000000001"},
            )

        with (
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.post",
                side_effect=fake_post,
            ),
            patch(
                "odoo.addons.l10n_br_dere.models.receita_integra.requests.get",
                side_effect=lambda url, **_kw: _FakeResponse(status_code=503, text=""),
            ),
        ):
            batch = declaration._send_events(
                declaration.event_ids.filtered(lambda ev: ev.event_type == "D-1001")
            )
        self.assertFalse(xsd_validator.validate_lote(batch.xml_content))
        self.assertTrue(batch.protocol)

    def test_store_xml_rejects_invalid_payload(self):
        declaration = self._create_declaration("2026-08")
        event = self.env["l10n_br_dere.event"].create(
            {
                "declaration_id": declaration.id,
                "event_type": "D-1199",
                "tp_amb": "2",
                "ver_aplic": "odoo-dere-18.0",
            }
        )
        with self.assertRaises(UserError) as error:
            event._store_xml(
                '<DeRE xmlns="http://www.dere.gov.br/schemas/evtFechMensal/v0_0_2">'
                '<evtFechMensal id="not-a-valid-id"/>'
                "</DeRE>"
            )
        self.assertIn("XSD", str(error.exception))
        self.assertFalse(event.xml_content)
