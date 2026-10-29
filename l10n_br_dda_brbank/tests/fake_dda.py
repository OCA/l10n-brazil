# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fake bank with DDA, registered in the brbank registry by the tests only."""

from decimal import Decimal

from brbank.dda import AdapterDda, CapacidadeDda, PaginaDebitos, ResumoDda, StatusDda

from odoo.addons.l10n_br_bank_connection.tests.fake_bank import FakeAdapter

FAKE_DDA = "dda_test_fake"
STATE = {}


def reset_state():
    STATE.clear()
    STATE.update(
        {
            "pages": [],  # pages of DebitoDda the listing answers
            "events": [],  # EventoDda the webhook parser answers
            "error": None,  # raised by the listing
            "stuck": None,  # cursor the listing answers as its own next
            "calls": [],  # (cnpj, desde, cursor) of each listing page
            "activation": [],  # "on" / "off"
        }
    )


reset_state()


class FakeDdaAdapter(FakeAdapter, AdapterDda):
    banco = "dda_fake"
    capacidades_dda = (
        CapacidadeDda.ATIVACAO
        | CapacidadeDda.CONSULTA
        | CapacidadeDda.RESUMO
        | CapacidadeDda.WEBHOOK
    )

    async def ativar_dda(self, cnpj):
        STATE["activation"].append("on")

    async def desativar_dda(self, cnpj):
        STATE["activation"].append("off")

    async def listar_debitos(self, cnpj, desde=None, cursor=None):
        STATE["calls"].append((cnpj, desde, cursor))
        if STATE["error"] is not None:
            raise STATE["error"]
        index = int(cursor or 0)
        pages = STATE["pages"]
        if index >= len(pages):
            return PaginaDebitos()
        following = str(index + 1) if index + 1 < len(pages) else None
        if STATE["stuck"] is not None and cursor == STATE["stuck"]:
            following = cursor  # a bank whose cursor never advances
        return PaginaDebitos(itens=tuple(pages[index]), cursor_proximo=following)

    async def resumo_debitos(self, cnpj):
        items = [debit for page in STATE["pages"] for debit in page]
        return ResumoDda(
            quantidade=len(items),
            valor_total=sum((debit.valor for debit in items), Decimal(0)),
            por_status={StatusDda.ABERTO: len(items)},
        )

    def parse_webhook_dda(self, corpo, cabecalhos=None):
        return list(STATE["events"])
