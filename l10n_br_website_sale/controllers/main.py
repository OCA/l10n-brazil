# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class L10nBrWebsiteSale(WebsiteSale):
    def _is_br_checkout(self, country_id):
        return (
            request.website.company_id.country_id.code == "BR"
            and request.env["res.country"].browse(country_id).code == "BR"
        )

    def _get_br_address_fields(self, fields):
        return list(
            dict.fromkeys(
                [field for field in fields if field not in ("city", "street")]
                + [
                    "state_id",
                    "city_id",
                    "zip",
                    "street_name",
                    "street_number",
                    "district",
                ]
            )
        )

    def _get_mandatory_fields_billing(self, country_id=False):
        fields = super()._get_mandatory_fields_billing(country_id)
        if self._is_br_checkout(country_id):
            return self._get_br_address_fields(fields) + ["vat"]
        return fields

    def _get_mandatory_fields_shipping(self, country_id=False):
        fields = super()._get_mandatory_fields_shipping(country_id)
        if self._is_br_checkout(country_id):
            return self._get_br_address_fields(fields)
        return fields

    def _update_so_external_taxes(self, order):
        # The 16.0 fiscal fields are computed from the operation on the line.
        # Apply the order's configured operation after the address is validated.
        if order.company_id.country_id.code == "BR" and order.fiscal_operation_id:
            lines = order.order_line.filtered(lambda line: not line.display_type)
            lines.filtered(lambda line: not line.fiscal_operation_id).write(
                {"fiscal_operation_id": order.fiscal_operation_id.id}
            )
        return super()._update_so_external_taxes(order)

    def _get_country_related_render_values(self, kw, render_values):
        values = super()._get_country_related_render_values(kw, render_values)
        br_company = request.website.company_id.country_id.code == "BR"
        checkout = render_values["checkout"]
        country = values["country"]
        if br_company and not country and "country_id" not in checkout:
            country = request.env.ref("base.br")
            mode = render_values["mode"][1]
            values.update(
                country=country,
                country_states=country.get_website_sale_states(mode=mode),
                countries=country.get_website_sale_countries(mode=mode),
            )
        br_address = br_company and bool(country) and country.code == "BR"
        cities = request.env["res.city"]
        if br_address and "state_id" in checkout and checkout["state_id"]:
            cities = cities.search([("state_id", "=", int(checkout["state_id"]))])
        values.update(br_company=br_company, br_address=br_address, cities=cities)
        return values

    def values_preprocess(self, values):
        data = super().values_preprocess(values)
        if self._is_br_checkout(data.get("country_id")):
            city = request.env["res.city"].sudo().browse(data.get("city_id")).exists()
            if (
                city
                and city.state_id.id == data.get("state_id")
                and city.country_id.id == data["country_id"]
            ):
                data["city"] = city.name
            else:
                data["city_id"] = False
        return data

    def values_postprocess(self, order, mode, values, errors, error_msg):
        result, errors, error_msg = super().values_postprocess(
            order, mode, values, errors, error_msg
        )
        if self._is_br_checkout(values.get("country_id")):
            fields = ["city_id", "street_name", "street_number", "district", "mobile"]
            if mode[1] == "billing":
                fiscal_fields = ["l10n_br_ie_code", "l10n_br_im_code", "vat"]
                for field in fiscal_fields:
                    if (
                        mode[0] == "edit"
                        and order.partner_id[field]
                        and not order.partner_id.can_edit_vat()
                    ):
                        result.pop(field, None)
                    else:
                        fields.append(field)
            for field in fields:
                if field in values and field not in errors:
                    result[field] = values[field]
        return result, errors, error_msg

    def checkout_form_validate(self, mode, all_form_values, data):
        errors, messages = super().checkout_form_validate(mode, all_form_values, data)
        if (
            self._is_br_checkout(data.get("country_id"))
            and mode[1] == "billing"
            and data.get("vat")
            and not cnpj_cpf.validar(data["vat"])
        ):
            errors["vat"] = "error"
            messages.append(_("Invalid CPF or CNPJ."))
        return errors, messages

    @http.route(
        ['/shop/state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, **kw):
        cities = request.env["res.city"].search([("state_id", "=", state.id)])
        return {"cities": [(city.id, city.name) for city in cities]}

    @http.route(
        "/l10n_br/zip_search_public",
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def zip_search(self, zipcode):
        try:
            result = request.env["l10n_br.zip"].sudo()._consultar_cep(zipcode)
        except UserError:
            result = {}
        return result or {"error": "zip"}
