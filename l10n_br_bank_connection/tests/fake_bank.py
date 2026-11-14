# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fake bank adapter, registered in the brbank registry by the tests only."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from brbank import BankAdapter, Capacidade, TabelaStatus
from brbank.erros import NaoSuportado

FAKE = "conn_test_fake"
FAKE_NO_SANDBOX = "conn_test_fake_no_sandbox"
STATE = {}


def reset_state():
    STATE.clear()
    STATE.update({"configs": [], "error": None, "result": "ok"})


reset_state()


@dataclass
class FakeConfig:
    conta: str
    client_id: str
    client_secret: str = field(repr=False)
    ambiente: str = "producao"
    cnpj_empresa: str = ""
    refresh_token: str = field(default="", repr=False)
    url_base_override: str | None = None
    armazem: Any = field(default=None, repr=False)
    ler_refresh_token: Callable[[], str] | None = field(default=None, repr=False)
    ao_renovar_refresh_token: Callable[[str], None] | None = field(
        default=None, repr=False
    )


class FakeAdapter(BankAdapter):
    banco = "fake_conn"
    capacidades = Capacidade.WEBHOOK
    tabela_status = TabelaStatus.criar("test", {})

    def __init__(self, config: FakeConfig, *, client=None):
        self.config = config
        STATE["configs"].append(config)

    async def registrar_titulo(self, titulo):
        raise NaoSuportado("fake")

    async def consultar_titulo(self, id_banco):
        raise NaoSuportado("fake")

    async def enviar_instrucao(self, id_banco, instrucao):
        raise NaoSuportado("fake")

    async def baixar_titulo(self, id_banco):
        raise NaoSuportado("fake")

    def parse_webhook(self, corpo, cabecalhos=None):
        return []

    async def ping(self):
        if STATE["error"] is not None:
            raise STATE["error"]
        return STATE["result"]


@dataclass
class FakeNoSandboxConfig:
    """A bank with a single environment: no `ambiente` key."""

    conta: str
    client_id: str


class FakeNoSandboxAdapter(FakeAdapter):
    def __init__(self, config: FakeNoSandboxConfig, *, client=None):
        super().__init__(config, client=client)
