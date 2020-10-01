# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


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
        return ["name", "email", "street", "country_id", "state_id", "city_id"]

    def _get_mandatory_shipping_fields(self):
        return ["name", "street", "country_id", "state_id", "city_id"]

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
            country_id = request.env['res.country'].search([('code', '=', 'BR')])
            res.qcontext['country'] = country_id
        return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(L10nBrWebsiteSale, self)\
            .values_postprocess(order, mode, values, errors, error_msg)
        if 'city_id' in values:
            new_values['city_id'] = values['city_id']
        return new_values, errors, error_msg

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
                website=True)
    def zip_search(self, zipcode):
        try:
            return request.env['l10n_br.zip'].sudo()._consultar_cep(zipcode)
        except Exception as e:
            return {
                'error': 'zip',
                'error_message': e,
                }
