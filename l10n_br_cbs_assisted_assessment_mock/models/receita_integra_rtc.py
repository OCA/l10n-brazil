# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from .mock_file import MOCK_TICKET_PREFIX, MOCK_URL_PREFIX


class ReceitaIntegraRtc(models.AbstractModel):
    _inherit = "l10n_br_cbs_assisted_assessment.client"

    def _open_request(self, company, service, return_url):
        if company.cbs_assessment_mock_mode:
            return self.env["l10n_br_cbs_assisted_assessment.mock.file"]._open_request(
                company, service
            )
        return super()._open_request(company, service, return_url)

    def _get_status(self, company, ticket):
        if self._is_mock_ticket(ticket):
            payload = self.env[
                "l10n_br_cbs_assisted_assessment.mock.file"
            ]._payload_for_ticket(ticket)
            if not payload:
                return {
                    "situacao": "ERRO",
                    "codigoErro": "MOCK-404",
                    "mensagemErro": _(
                        "The mock file for ticket %s was not found.", ticket
                    ),
                }
            return {"situacao": "CONCLUIDA"}
        return super()._get_status(company, ticket)

    def _get_download_link(self, company, ticket):
        if self._is_mock_ticket(ticket):
            return {
                "urlAssinada": f"{MOCK_URL_PREFIX}{ticket}",
                "urlAssinadaExpiraEm": "2099-01-01T00:00:00Z",
            }
        return super()._get_download_link(company, ticket)

    def _download(self, signed_url):
        if (signed_url or "").startswith(MOCK_URL_PREFIX):
            ticket = signed_url[len(MOCK_URL_PREFIX) :]
            payload = self.env[
                "l10n_br_cbs_assisted_assessment.mock.file"
            ]._payload_for_ticket(ticket)
            if not payload:
                raise UserError(_("The mock file for ticket %s was not found.", ticket))
            return payload
        return super()._download(signed_url)

    def _is_mock_ticket(self, ticket):
        return (ticket or "").startswith(MOCK_TICKET_PREFIX)
