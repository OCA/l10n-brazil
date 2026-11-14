# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from brbank import registro

from .fake_bank import (
    FAKE,
    FAKE_NO_SANDBOX,
    FakeAdapter,
    FakeNoSandboxAdapter,
    reset_state,
)

MODEL = "l10n_br_bank_connection.connection"


class ConnectionCommon:
    @classmethod
    def _setup_connection(cls):
        cls.env = cls.env(
            context=dict(cls.env.context, tracking_disable=True, lang="en_US")
        )
        registro.registrar_adapter(FAKE, FakeAdapter)
        registro.registrar_adapter(FAKE_NO_SANDBOX, FakeNoSandboxAdapter)
        cls.addClassCleanup(lambda: registro._manuais.pop(FAKE, None))
        cls.addClassCleanup(lambda: registro._manuais.pop(FAKE_NO_SANDBOX, None))
        reset_state()
        cls.Connection = cls.env[MODEL]

    @classmethod
    def _create_connection(cls, **values):
        return cls.Connection.create(
            dict(
                {
                    "name": "Fake bank",
                    "adapter": FAKE,
                    "environment": "test",
                    "cnpj": "91.300.766/0001-47",
                    "client_id": "client-id",
                    "client_secret": "client-secret",
                },
                **values,
            )
        )
