# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fake bank adapter, registered in the brbank registry by the tests only."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from brbank import (
    BankAdapter,
    Capacidade,
    EventoCanonico,
    StatusCanonico,
    TabelaStatus,
    TipoInstrucao,
    TituloRegistrado,
)
from brbank.erros import NaoSuportado, Validacao

BANK = {}


def reset_bank():
    BANK.clear()
    BANK.update(
        {
            "titles": {},
            "calls": [],
            "register_error": None,
            "unsupported": set(),
            "instruction_error": None,
            "register_status": StatusCanonico.REGISTRADO,
        }
    )


reset_bank()


@dataclass
class FakeConfig:
    conta: str
    client_id: str
    client_secret: str = field(repr=False)
    numero_cliente: int
    ambiente: str = "producao"
    chave_api: str = field(default="", repr=False)
    obter_txid: Callable[[str], str | None] | None = field(default=None, repr=False)


class FakeAdapter(BankAdapter):
    banco = "fake"
    capacidades = (
        Capacidade.ALTERACAO | Capacidade.BAIXA | Capacidade.PDF | Capacidade.WEBHOOK
    )
    tabela_status = TabelaStatus.criar("test", {})

    def __init__(self, config: FakeConfig, *, client=None):
        self.config = config
        self.client = client

    def _registered(self, id_banco):
        title = BANK["titles"][id_banco]
        if title["status"] is StatusCanonico.PENDENTE_REGISTRO:
            return TituloRegistrado(
                banco=self.banco, id_banco=id_banco, status=title["status"]
            )
        return TituloRegistrado(
            banco=self.banco,
            id_banco=id_banco,
            status=title["status"],
            seu_numero=title["seu_numero"],
            nosso_numero=f"NN{id_banco}",
            linha_digitavel=f"00190.00009 {id_banco}",
            codigo_barras=f"0019{id_banco}",
            pix_copia_cola=f"00020101PIX{id_banco}",
            txid=f"TX{id_banco}",
            valor_pago=title.get("valor_pago"),
            data_pagamento=title.get("data_pagamento"),
            resposta_bruta={"nomePagador": "Fulano", "situacao": title["status"]},
        )

    async def registrar_titulo(self, titulo):
        BANK["calls"].append(("registrar", titulo.chave_idempotencia))
        if BANK["register_error"] is not None:
            raise BANK["register_error"]
        id_banco = f"B{titulo.seu_numero}"
        BANK["titles"].setdefault(
            id_banco,
            {
                "status": BANK["register_status"],
                "seu_numero": titulo.seu_numero,
                "valor": titulo.valor,
                "vencimento": titulo.vencimento,
                "pagador_documento": titulo.pagador.documento,
            },
        )
        return self._registered(id_banco)

    async def consultar_titulo(self, id_banco):
        BANK["calls"].append(("consultar", id_banco))
        return self._registered(id_banco)

    async def enviar_instrucao(self, id_banco, instrucao):
        BANK["calls"].append(("instrucao", instrucao.tipo.value))
        BANK["calls"].append(("txid", self.config.obter_txid(id_banco)))
        if instrucao.tipo in BANK["unsupported"]:
            raise NaoSuportado(f"fake: {instrucao.tipo.value} not supported")
        if BANK["instruction_error"] is not None:
            raise BANK["instruction_error"]
        if instrucao.tipo is TipoInstrucao.PRORROGACAO:
            BANK["titles"][id_banco]["vencimento"] = instrucao.nova_data_vencimento
        return self._registered(id_banco)

    async def baixar_titulo(self, id_banco):
        BANK["calls"].append(("baixar", id_banco))
        BANK["titles"][id_banco]["status"] = StatusCanonico.BAIXADO
        return self._registered(id_banco)

    def parse_webhook(self, corpo, cabecalhos=None):
        BANK["calls"].append(("webhook", None))
        try:
            items = json.loads(corpo)
        except ValueError as error:
            raise Validacao("fake: webhook is not JSON") from error
        return [
            EventoCanonico(
                banco=self.banco,
                referencia=item["ref"],
                tipo=StatusCanonico(item["status"]),
                valor_pago=Decimal(item["paid"]) if item.get("paid") else None,
                resposta_bruta=item,
            )
            for item in items
        ]

    async def obter_pdf(self, id_banco):
        return b"%PDF-1.4 fake boleto"


class FakeBasicAdapter(FakeAdapter):
    """A bank that only writes titles off: no instructions, no webhook."""

    banco = "fake_basic"
    capacidades = Capacidade.BAIXA
