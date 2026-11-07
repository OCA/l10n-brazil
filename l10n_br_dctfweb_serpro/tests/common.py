# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

MOCK_POST = "odoo.addons.l10n_br_dctfweb_serpro.models.integra_contador.requests.post"


class FakeResponse:
    """The shape of the answer the platform gives, without the network."""

    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


def answer(data=None, status=200, messages=None, http_status=200):
    """Build an answer whose "dados" is a JSON string, as the platform does."""
    payload = {
        "status": status,
        "mensagens": messages
        or [{"codigo": "[Sucesso]", "texto": "Requisicao efetuada com sucesso."}],
    }
    if data is not None:
        payload["dados"] = data if isinstance(data, str) else json.dumps(data)
    return FakeResponse(payload, http_status)


class TestSerproCommon(AccountTestInvoicingCommon):
    """A company with credentials and an assessed MIT to send."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.company = cls.company_data["company"]
        cls.company.write({"cnpj_cpf": "12.345.678/0001-95"})
        cls.company.sudo().write(
            {
                "serpro_environment": "trial",
                "serpro_consumer_key": "key",
                "serpro_consumer_secret": "secret",
                "serpro_access_token": "a-token",
                "serpro_warn_cost": False,
            }
        )
        cls.code_pis = cls.env.ref("l10n_br_dctfweb.revenue_code_810902")
        cls.mit = cls.env["l10n_br_dctfweb.assessment"].create(
            {
                "company_id": cls.company.id,
                "year": 2026,
                "month": "7",
                "pj_qualification": "1",
                "profit_taxation": "3",
                "monetary_variation": "2",
                "pis_cofins_regime": "2",
                "responsible_cpf": "07206845000",
            }
        )
        cls.env["l10n_br_dctfweb.debit"].create(
            {
                "assessment_id": cls.mit.id,
                "revenue_code_id": cls.code_pis.id,
                "amount": 1000.0,
            }
        )
        cls.mit.state = "assessed"

    @classmethod
    def _no_expired_token(cls, company):
        """Keep the token alive so no test hits the token endpoint."""
        company.sudo().write(
            {
                "serpro_access_token": "a-token",
                "serpro_token_expiration": "2099-01-01 00:00:00",
            }
        )
