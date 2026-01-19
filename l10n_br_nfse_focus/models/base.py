# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Base class for FocusNFE NFSe operations."""

import requests

from odoo import _, models
from odoo.exceptions import UserError


class FocusnfeNfseBase(models.AbstractModel):
    """Base class for FocusNFE NFSe operations with shared HTTP request logic."""

    _name = "focusnfe.nfse.base"
    _description = "FocusNFE NFSE Base"

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
                msg = payload.get("mensagem") or ""
                raise UserError(
                    f"Error communicating with {service_name} service: {msg}"
                )
            response.raise_for_status()  # Raises an error for 4xx/5xx responses
            return response
        except requests.HTTPError as e:
            raise UserError(
                _("Error communicating with %(service)s service: %(error)s")
                % {"service": service_name, "error": e}
            ) from e
