# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale

BR_ADDRESS_FIELDS = {"city_id", "district", "street_name", "street_number"}
BR_TAX_REGISTRATIONS = ("l10n_br_ie_code", "l10n_br_im_code")


class L10nBrWebsiteSale(WebsiteSale):
    def _is_br_checkout(self, country):
        return (
            request.website.sudo().company_id.country_id.code == "BR"
            and country.code == "BR"
        )

    def _get_mandatory_address_fields(self, country_sudo):
        fields = super()._get_mandatory_address_fields(country_sudo)
        if self._is_br_checkout(country_sudo):
            fields = (
                (fields - {"street", "city"}) | BR_ADDRESS_FIELDS | {"state_id", "zip"}
            )
        return fields

    def _get_mandatory_billing_address_fields(self, country_sudo):
        fields = super()._get_mandatory_billing_address_fields(country_sudo)
        # The portal profile adds its Brazilian fields to CustomerPortal, which the
        # checkout also inherits. Here the address country controls those fields.
        portal_fields = set(self._get_mandatory_fields())
        standard_portal_fields = set(CustomerPortal._get_mandatory_fields(self))
        fields -= portal_fields - standard_portal_fields
        fields |= self._get_mandatory_address_fields(country_sudo)
        if self._is_br_checkout(country_sudo):
            fields -= {"street", "city"}
            fields.add("vat")
        return fields

    def _prepare_address_form_values(
        self, order_sudo, partner_sudo, address_type, use_delivery_as_billing, **kwargs
    ):
        values = super()._prepare_address_form_values(
            order_sudo, partner_sudo, address_type, use_delivery_as_billing, **kwargs
        )
        br_company = order_sudo.company_id.country_id.code == "BR"
        if not br_company:
            return values
        country = values["country"] or request.env.ref("base.br")
        br_address = country.code == "BR"
        cities = request.env["res.city"].sudo()
        if br_address and values["state_id"]:
            cities = cities.search([("state_id", "=", values["state_id"])])
        values.update(
            country=country,
            country_states=country.state_ids,
            br_company=br_company,
            br_address=br_address,
            br_cities=cities,
        )
        return values

    def _parse_form_data(self, form_data):
        values, extra = super()._parse_form_data(form_data)
        country = request.env["res.country"].browse(values.get("country_id"))
        if self._is_br_checkout(country):
            for field in BR_ADDRESS_FIELDS | {"mobile", *BR_TAX_REGISTRATIONS}:
                if field in form_data:
                    value = form_data[field].strip()
                    values[field] = (
                        (int(value) if value.isdecimal() else False)
                        if field == "city_id"
                        else value
                    )
                    extra.pop(field, None)
            # The split fields carry the actual address, even when editing a contact.
            for field in ("street", "city"):
                values.pop(field, None)
        return values, extra

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **kwargs,
    ):
        country = request.env["res.country"].browse(address_values.get("country_id"))
        br_address = self._is_br_checkout(country)
        if br_address and (
            (address_type != "billing" and not use_delivery_as_billing)
            or (partner_sudo and not partner_sudo.can_edit_vat())
        ):
            for field in BR_TAX_REGISTRATIONS:
                address_values.pop(field, None)

        invalid, missing, messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address,
            **kwargs,
        )
        if br_address:
            if city_id := address_values.get("city_id"):
                city = request.env["res.city"].sudo().browse(city_id).exists()
                if (
                    not city
                    or city.state_id.id != address_values.get("state_id")
                    or city.country_id != country
                ):
                    invalid.add("city_id")
                    messages.append(_("Select a city in the chosen state."))
                else:
                    address_values["city"] = city.name
            if (
                (address_type == "billing" or use_delivery_as_billing)
                and address_values.get("vat")
                and "vat" not in invalid
                and not cnpj_cpf.validar(address_values["vat"])
            ):
                invalid.add("vat")
                messages.append(_("Invalid CPF or CNPJ."))
        return invalid, missing, messages

    @http.route(
        ['/shop/state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        readonly=True,
    )
    def state_infos(self, state, **kw):
        if not self._is_br_checkout(state.country_id):
            return {"cities": []}
        # Only public municipality names and IDs of the selected state are exposed.
        cities = request.env["res.city"].sudo().search([("state_id", "=", state.id)])
        return {"cities": [(city.id, city.name) for city in cities]}

    @http.route(
        "/l10n_br/zip_search_public",
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def checkout_zip_search(self, zipcode, **kwargs):
        try:
            result = request.env["l10n_br.zip"].sudo()._consultar_cep(zipcode)
        except UserError:
            result = {}
        return result or {"error": "zip"}
