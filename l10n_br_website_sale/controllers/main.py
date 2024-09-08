# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from erpbrasil.base.fiscal import cnpj_cpf

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class L10nBrWebsiteSale(WebsiteSale):
    def _get_country_code(self, country_id):
        return request.env["res.country"].browse(country_id).code

    # overwrite confirm_order
    @http.route(
        ["/shop/confirm_order"], type="http", auth="public", website=True, sitemap=False
    )
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        for line in order.order_line:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        return super().confirm_order(**post)

    def _get_mandatory_fields_billing(self, country_id=False):
        req = super()._get_mandatory_fields_billing(country_id)
        company_country_code = request.website.company_id.country_id.code
        if country_id:
            if (
                self._get_country_code(country_id) == "BR"
                and company_country_code == "BR"
            ):
                req.remove("city")
                req.remove("street")
                extension = [
                    "street_name",
                    "street_number",
                    "district",
                    "country_id",
                    "state_id",
                    "city_id",
                    "zip",
                    "cnpj_cpf",
                ]
                req.extend(extension)
        return req

    def _get_mandatory_fields_shipping(self, country_id=False):
        req = super()._get_mandatory_fields_shipping(country_id)
        company_country_code = request.website.company_id.country_id.code
        if country_id:
            if (
                self._get_country_code(country_id) == "BR"
                and company_country_code == "BR"
            ):
                req.remove("city")
                req.remove("street")
                extension = [
                    "country_id",
                    "state_id",
                    "city_id",
                    "zip",
                    "street_name",
                    "street_number",
                    "district",
                ]
                req.extend(extension)
        return req

    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="public",
        website=True,
        sitemap=False,
    )
    def address(self, **kw):
        if kw and kw.get("city_id"):
            city_id = request.env["res.city"].sudo().browse(int(kw.get("city_id")))
            if city_id:
                kw["city"] = city_id.name
        res = super().address(**kw)
        if "submitted" not in kw:
            country_id = request.env["res.country"].search([("code", "=", "BR")])
            res.qcontext["country"] = country_id
        # initiate form with city filled
        if (
            "checkout" in res.qcontext
            and "city_id" in res.qcontext["checkout"]
            and res.qcontext["checkout"]["city_id"]
        ):
            state_id = res.qcontext["checkout"]["state_id"]
            if not isinstance(state_id, str):
                state_id = state_id.id
            elif state_id:
                state_id = int(state_id)
            else:
                return res
            cities = request.env["res.city"].search([("state_id", "=", state_id)])
            res.qcontext["cities"] = cities
        return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super().values_postprocess(
            order, mode, values, errors, error_msg
        )

        # Check if the current country is not Brazil and remove specific errors
        if self._get_country_code(new_values.get("country_id")) != "BR":
            error_fields = ["state_id", "city_id", "cnpj_cpf", "inscr_est", "inscr_mun"]
            for field in error_fields:
                errors.pop(field, None)

        # Expected fields that may be updated in new_values if not present in errors
        expected_fields = [
            "city_id",
            "cnpj_cpf",
            "company_type",
            "street_name",
            "street_number",
            "district",
            "mobile",
            "inscr_est",
            "inscr_mun",
            "vat",
        ]

        # Update new_values for each expected field if it exists in values and not in
        # errors
        for field in expected_fields:
            if field in values and field not in errors:
                new_values[field] = values[field]

        return new_values, errors, error_msg

    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super().checkout_form_validate(
            mode, all_form_values, data
        )
        if "cnpj_cpf" in data:
            if (
                "country_id" in data
                and self._get_country_code(data["country_id"]) == "BR"
            ):
                order = request.website.sale_get_order()
                if order.partner_id.is_company:
                    if not cnpj_cpf.validar(data["cnpj_cpf"]):
                        error["cnpj_cpf"] = "error"
                        error_message.append("CNPJ Inválido")
                elif not cnpj_cpf.validar(data["cnpj_cpf"]):
                    error["cnpj_cpf"] = "error"
                    error_message.append("CPF Inválido")

                if "cnpj_cpf" not in error:
                    all_form_values["cnpj_cpf"] = data["cnpj_cpf"]
        if "vat" in data and data["vat"]:
            if (
                "country_id" in data
                and self._get_country_code(data["country_id"]) == "BR"
            ):
                if not cnpj_cpf.validar(data["vat"]):
                    error["cnpj_cpf"] = "error"
                    error_message.append("VAT Inválido")
            if "vat" not in error:
                all_form_values["vat"] = data["vat"]

        return error, error_message

    @http.route(
        ['/shop/country_infos/<model("res.country"):country>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def country_infos(self, country, mode, **kw):
        res = super().country_infos(country, mode, **kw)
        res["country_code"] = country.code
        return res

    @http.route(
        ['/shop/state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, **kw):
        cities = request.env["res.city"].search([("state_id", "=", state.id)])
        return dict(
            cities=[(ct.id, ct.name) for ct in cities],
        )

    @http.route(
        "/l10n_br/zip_search_public",
        type="json",
        auth="public",
        website=True,
        csrf=True,
    )
    def zip_search(self, zipcode):
        try:
            return request.env["l10n_br.zip"].sudo()._consultar_cep(zipcode)
        except Exception as e:
            return {
                "error": "zip",
                "error_message": e,
            }
