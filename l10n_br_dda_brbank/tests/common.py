# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from brbank import registro
from brbank.dda import DebitoDda, EventoDda, StatusDda, TipoEventoDda

from odoo import fields
from odoo.tests import tagged

from odoo.addons.l10n_br_bank_connection.tests.common import ConnectionCommon
from odoo.addons.l10n_br_dda.tests.common import PAYER, DdaCommon

from ..utils import source_key
from .fake_dda import FAKE_DDA, STATE, FakeDdaAdapter, reset_state

CRON_TRIGGER = "odoo.addons.base.models.ir_cron.ir_cron._trigger"
EVENT_LOGGER = "odoo.addons.l10n_br_dda_brbank.models.dda_event"
CONNECTION_LOGGER = "odoo.addons.l10n_br_dda_brbank.models.bank_connection"
VENDOR = "94623756000130"


def make_debit(number, **values):
    """A `DebitoDda` of the fake bank; the digitable line is only shaped."""
    data = {
        "banco": "dda_fake",
        "id_banco": f"bank-{number}",
        "cnpj_pagador": PAYER,
        "linha_digitavel": "3888%043d" % number,
        "beneficiario_documento": VENDOR,
        "beneficiario_nome": f"Vendor {number}",
        "valor": Decimal("100.00") + number,
        "vencimento": date.today() + timedelta(days=10),
        "status": StatusDda.ABERTO,
    }
    data.update(values)
    return DebitoDda(**data)


def make_event(event_id, kind, *debits, **values):
    data = {
        "banco": "dda_fake",
        "id_evento": event_id,
        "tipo": kind,
        "cnpj_pagador": PAYER,
        "debitos": tuple(debits),
    }
    data.update(values)
    return EventoDda(**data)


@tagged("post_install", "-at_install")
class DdaBrbankCommon(DdaCommon, ConnectionCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_connection()
        registro.registrar_adapter(FAKE_DDA, FakeDdaAdapter)
        cls.addClassCleanup(lambda: registro._manuais.pop(FAKE_DDA, None))
        cls.Event = cls.env["l10n_br_dda.event"]
        cls.NEW = TipoEventoDda.DEBITO_NOVO
        cls.CHANGED = TipoEventoDda.DEBITO_ALTERADO
        cls.PAID = TipoEventoDda.DEBITO_PAGO
        cls.DISABLED = TipoEventoDda.DDA_DESATIVADO
        cls.ENABLED = TipoEventoDda.DDA_ATIVADO

    def setUp(self):
        super().setUp()
        reset_state()
        # The demo connection (simulator on localhost) must not join the crons.
        self.env["l10n_br_bank_connection.connection"].sudo().with_context(
            active_test=False
        ).search([]).write({"dda_enabled": False})
        self.connection = self.new_connection()

    @classmethod
    def new_connection(cls, **values):
        return cls._create_connection(
            **dict(
                {
                    "name": "Fake DDA bank",
                    "adapter": FAKE_DDA,
                    "cnpj": PAYER,
                    "company_id": cls.company.id,
                },
                **values,
            )
        )

    def enable(self, connection=None):
        connection = connection or self.connection
        connection.write({"dda_enabled": True, "state": "connected"})
        return connection

    def webhook(self, *events, connection=None):
        """Hand events to the webhook hook; returns (counts, trigger mock)."""
        STATE["events"] = list(events)
        with patch(CRON_TRIGGER) as trigger:
            counts = (connection or self.connection)._l10n_br_bank_handle_webhook(
                b"{}", {}
            )
        return counts, trigger

    def store(self, *events, connection=None):
        counts, _trigger = self.webhook(*events, connection=connection)
        return counts

    def run_events(self):
        with patch(CRON_TRIGGER) as trigger:
            self.Event._cron_process_events()
        return trigger

    def event_of(self, event_id, connection=None):
        return self.Event.search(
            [
                ("connection_id", "=", (connection or self.connection).id),
                ("event_id", "=", event_id),
            ]
        )

    def debits_of(self, connection=None):
        connection = connection or self.connection
        return self.env["l10n_br_dda.debit"].search(
            [("source_ids.source_key", "=", source_key(connection))]
        )

    @staticmethod
    def minutes_ahead(event):
        return (event.next_attempt_at - fields.Datetime.now()) / timedelta(minutes=1)
