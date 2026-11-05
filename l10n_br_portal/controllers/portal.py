# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class L10nBrPortal(CustomerPortal):
    def _get_mandatory_address_fields(self, country_sudo):
        field_names = super()._get_mandatory_address_fields(country_sudo)
        if country_sudo.code == "BR":
            field_names = (field_names - {"street", "city"}) | {
                "street_name",
                "street_number",
                "district",
                "city_id",
                "state_id",
            }
        return field_names

    def _get_mandatory_billing_address_fields(self, country_sudo):
        field_names = super()._get_mandatory_billing_address_fields(country_sudo)
        if country_sudo.code == "BR":
            field_names |= {"vat"}
        return field_names

    def _prepare_address_form_values(self, *args, **kwargs):
        values = super()._prepare_address_form_values(*args, **kwargs)
        values["cities"] = request.env["res.city"].sudo().search([])
        return values

    @http.route("/l10n_br/zip_search", type="jsonrpc", auth="user", website=True)
    def zip_search(self, zipcode):
        try:
            return request.env["l10n_br.zip"].sudo()._consultar_cep(zipcode)
        except Exception as e:
            return {
                "error": "zip",
                "error_message": e,
            }
