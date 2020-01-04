# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class L10nBrPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = list(
        set(CustomerPortal.MANDATORY_BILLING_FIELDS)
    ) + [
        "state_id", "city_id", "district", "street_number", "legal_name",
        "cnpj_cpf", "zipcode", "inscr_est"
    ]
    OPTIONAL_BILLING_FIELDS = list(
        set(CustomerPortal.OPTIONAL_BILLING_FIELDS) - set(["state_id"])
    ) + ["inscr_mun", "street2", "mobile"]

    def _prepare_portal_layout_values(self):
        values = super(L10nBrPortal, self)._prepare_portal_layout_values()
        cities = request.env['res.city'].sudo().search([])
        values.update({
            'cities': cities,
        })
        return values

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        if post and post.get('city_id'):
            city_id = request.env['res.city'].sudo().browse(
                int(post.get('city_id')))
            if city_id:
                post['city'] = city_id.name
        res = super(L10nBrPortal, self).account(redirect, **post)
        return res

    @http.route('/l10n_br/zip_search', type='json', auth="user", website=True)
    def zip_search(self, zipcode):
        try:
            return request.env['l10n_br.zip'].sudo()._consultar_cep(zipcode)
        except Exception as e:
            return {
                'error': 'zip',
                'error_message': e,
            }
