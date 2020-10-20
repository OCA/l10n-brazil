# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)
try:
    from erpbrasil.base.fiscal import cnpj_cpf
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class L10nBrWebsiteSale(WebsiteSale):

    # overwrite confirm_order
    @http.route(['/shop/confirm_order'], type='http', auth="public",
                website=True, sitemap=False)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        for line in order.order_line:
            line._onchange_product_id_fiscal()
            line._onchange_commercial_quantity()
            line._onchange_ncm_id()
            line._onchange_fiscal_operation_id()
            line._onchange_fiscal_operation_line_id()
            line._onchange_fiscal_taxes()

        return super(L10nBrWebsiteSale, self).confirm_order(**post)

    def _get_mandatory_billing_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_billing_fields()
        order = request.website.sale_get_order()
        if order.partner_invoice_id.country_id and \
                order.partner_invoice_id.country_id.code == 'BR':
            if 'city' in res:
                res.remove('city')
            extension = [
                "name",
                "email",
                "street",
                "street_number",
                "district",
                "country_id",
                "state_id",
                "city_id",
                "zip",
                "cnpj_cpf",
                "company_type"
                ]
            res.extend(extension)
        return res

    def _get_mandatory_shipping_fields(self):
        res = super(L10nBrWebsiteSale, self)._get_mandatory_shipping_fields()
        order = request.website.sale_get_order()
        if order.partner_shipping_id.country_id and \
                order.partner_shipping_id.country_id.code == 'BR':
            if 'city' in res:
                res.remove('city')
            extension = [
                "name",
                "street",
                "country_id",
                "state_id",
                "city_id",
                "zip",
                "street_number",
                "district"
                ]
            res.extend(extension)
        return res

    @http.route(['/shop/address'], type='http', methods=['GET', 'POST'],
                auth="public", website=True, sitemap=False)
    def address(self, **kw):
        if kw and kw.get('city_id'):
            city_id = request.env['res.city'].sudo().browse(
                int(kw.get('city_id')))
            if city_id:
                kw['city'] = city_id.name
        res = super(L10nBrWebsiteSale, self).address(**kw)
        if 'submitted' not in kw:
            country_id = request.env['res.country'].search(
                [('code', '=', 'BR')])
            res.qcontext['country'] = country_id
        # initiate form with city filled
        if 'checkout' in res.qcontext and 'city_id' in res.qcontext[
                'checkout'] and res.qcontext['checkout']['city_id']:
            state_id = res.qcontext['checkout']['state_id']
            if type(state_id) != str:
                state_id = state_id.id
            elif state_id:
                state_id = int(state_id)
            else:
                return res
            cities = request.env['res.city'].search(
                [('state_id', '=', state_id)])
            res.qcontext['cities'] = cities
        return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(L10nBrWebsiteSale, self) \
            .values_postprocess(order, mode, values, errors, error_msg)
        if 'country_id' in new_values and new_values['country_id'] != '31':
            if 'state_id' in errors:
                errors.pop('state_id', None)
            if 'city_id' in errors:
                errors.pop('city_id', None)
            if 'cnpj_cpf' in errors:
                errors.pop('city_id', None)

        if 'city_id' in values:
            new_values['city_id'] = values['city_id']
        if 'cnpj_cpf' in values and 'cnpj_cpf' not in errors:
            new_values['cnpj_cpf'] = values['cnpj_cpf']
        if 'company_type' in values and 'company_type' not in errors:
            new_values['company_type'] = values['company_type']
        if 'street_number' in values:
            new_values['street_number'] = values['street_number']
        if 'district' in values:
            new_values['district'] = values['district']
        return new_values, errors, error_msg

    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super(L10nBrWebsiteSale, self) \
            .checkout_form_validate(mode, all_form_values, data)

        if 'cnpj_cpf' in data:
            if 'country_id' in data and data['country_id'] == '31':
                order = request.website.sale_get_order()
                if order.partner_id.is_company:
                    if not cnpj_cpf.validar(data['cnpj_cpf']):
                        error['cnpj_cpf'] = 'error'
                        error_message.append("CNPJ Inválido")
                elif not cnpj_cpf.validar(data['cnpj_cpf']):
                    error['cnpj_cpf'] = 'error'
                    error_message.append("CPF Inválido")

                if 'cnpj_cpf' not in error:
                    all_form_values['cnpj_cpf'] = data['cnpj_cpf']

        return error, error_message

    @http.route(['/shop/country_infos/<model("res.country"):country>'],
                type='json', auth="public", methods=['POST'], website=True)
    def country_infos(self, country, mode, **kw):
        return dict(
            fields=country.get_address_fields(),
            states=[(st.id, st.name, st.code) for st in
                    country.get_website_sale_states(mode=mode)],
            phone_code=country.phone_code
            )

    @http.route(['/shop/state_infos/<model("res.country.state"):state>'],
                type='json', auth="public", methods=['POST'], website=True)
    def state_infos(self, state, **kw):
        cities = request.env['res.city'].search([('state_id', '=', state.id)])
        return dict(
            cities=[(ct.id, ct.name) for ct in cities],
            )

    @http.route('/l10n_br/zip_search_public', type='json', auth="public",
                website=True, csrf=True)
    def zip_search(self, zipcode):
        try:
            return request.env['l10n_br.zip'].sudo()._consultar_cep(zipcode)
        except Exception as e:
            return {
                'error': 'zip',
                'error_message': e,
                }
