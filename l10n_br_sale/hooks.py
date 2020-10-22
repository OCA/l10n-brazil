# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, tools, SUPERUSER_ID


def post_init_hook(cr, registry):

    if not tools.config['without_demo']:
        env = api.Environment(cr, SUPERUSER_ID, {})
        sale_orders = env['sale.order'].search(
            [('company_id', '!=', env.ref('base.main_company').id)])

        for order in sale_orders:
            defaults = order.sudo(
                user=order.user_id.id).default_get(order._fields)
            defaults.update({
                'name': order.name,
                'fiscal_operation_id': order.fiscal_operation_id.id
            })
            order.write(defaults)
