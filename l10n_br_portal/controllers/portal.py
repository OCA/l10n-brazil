# Copyright 2016 KMEE - Luis Felipe Miléo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http, _
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class L10nBrPortal(CustomerPortal):
    MANDATORY_BILLING_FIELDS = list(
        set(CustomerPortal.MANDATORY_BILLING_FIELDS) - set(["city"])
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
        res = super(L10nBrPortal, self).account(**post)
        return res
