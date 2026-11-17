# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Base class for FocusNFE NFSe operations."""

import re

import requests

from odoo import _, models
from odoo.exceptions import UserError

FOCUS_XSD_ERROR_LINE_RE = re.compile(
    r"^\d+:\d+:\s*ERROR:\s*(?P<descricao>.+?)" r"(?:\s*--\s*xpath:\s*(?P<xpath>.+))?$",
    re.MULTILINE,
)


class FocusnfeNfseBase(models.AbstractModel):
    """Base class for FocusNFE NFSe operations with shared HTTP request logic."""

    _name = "focusnfe.nfse.base"
    _description = "FocusNFE NFSE Base"

    def _format_focus_nfse_message(self, raw_message):
        """Format a FocusNFE error message for display to the end user.

        FocusNFE sometimes returns raw XSD schema validation output
        (e.g. "42:0: ERROR: Element '...' -- xpath: /DPS/...") instead of a
        human-readable message. When that pattern is detected, each error
        line is turned into a labeled block; otherwise the message is
        returned unchanged.

        Args:
            raw_message (str): The raw message from the FocusNFE API.

        Returns:
            str: The formatted message.
        """
        non_empty_lines = [line for line in raw_message.splitlines() if line.strip()]
        matches = FOCUS_XSD_ERROR_LINE_RE.findall(raw_message)
        if len(matches) != len(non_empty_lines):
            return raw_message  # not every line is an XSD error, leave as-is

        blocks = []
        for descricao, xpath in matches:
            block = _("Error: %s") % descricao
            if xpath:
                block += "\n" + _("Field: %s") % xpath
            blocks.append(block)
        return "\n\n".join(blocks)

    def _make_focus_nfse_http_request(
        self, method, url, token, data=None, params=None, service_name="NFSe"
    ):
        """Perform a generic HTTP request.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            url (str): The URL to which the request is sent.
            token (str): The authentication token for the service.
            data (dict, optional): The payload to send in the request body.
                Defaults to None.
            params (dict, optional): The URL parameters to append to the URL.
                Defaults to None.
            service_name (str): Name of the service for error messages.

        Returns:
            requests.Response: The response object from the requests library.

        Raises:
            UserError: If the HTTP request fails with a 4xx/5xx response.
        """
        auth = (token, "")
        try:
            response = requests.request(  # pylint: disable=external-request-timeout
                method,
                url,
                data=data,
                params=params,
                auth=auth,
            )
            if response.status_code == 422:
                payload = response.json()
                raise UserError(
                    _("Error communicating with %(service)s service: %(error)s")
                    % {
                        "service": service_name,
                        "error": self._format_focus_nfse_message(
                            payload.get("mensagem") or ""
                        ),
                    }
                )
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            return response
        except requests.HTTPError as e:
            detail = self._extract_focus_nfse_error_detail(e.response)
            raise UserError(
                _("Error communicating with %(service)s service: %(error)s%(detail)s")
                % {
                    "service": service_name,
                    "error": e,
                    "detail": f" - {detail}" if detail else "",
                }
            ) from e

    @staticmethod
    def _extract_focus_nfse_error_detail(response):
        """Extract a human-readable detail from a FocusNFE error response body.

        The FocusNFE API usually returns a JSON body with a "mensagem" key
        (or an "erros" list) describing the actual cause of a failure, which
        is otherwise lost when only the HTTP status line is reported.

        Args:
            response (requests.Response): The error response, if available.

        Returns:
            str: The extracted message, or an empty string if unavailable.
        """
        if response is None:
            return ""
        try:
            payload = response.json()
        except ValueError:
            return response.text or ""
        if isinstance(payload, dict):
            erros = payload.get("erros")
            if erros:
                return "; ".join(
                    erro.get("mensagem", "") for erro in erros if isinstance(erro, dict)
                )
            return payload.get("mensagem") or str(payload)
        return str(payload)
