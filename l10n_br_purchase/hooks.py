# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, tools, SUPERUSER_ID


def post_init_hook(cr, registry):

    if not tools.config['without_demo']:
        env = api.Environment(cr, SUPERUSER_ID, {})
        purchase_orders = env['purchase.order'].search(
            [('company_id', '!=', env.ref('base.main_company').id)])

        for order in purchase_orders:
            defaults = order.with_context(
                company_id=order.company_id.id).default_get(order._fields)
            defaults.update({
                'name': order.name,
                'company_id': order.company_id.id,
                'fiscal_operation_id': order.fiscal_operation_id.id,
            })
            order.write(defaults)
