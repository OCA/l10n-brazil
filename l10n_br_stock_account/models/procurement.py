# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2016  Luis Felipe Mileo - KMEE                                #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    @api.model
    def _run_move_create(self, procurement):
        result = super(ProcurementOrder, self)._run_move_create(procurement)
        if (procurement.rule_id and procurement.rule_id.fiscal_category_id and
                procurement.move_dest_id):
            ctx = dict(self.env.context)
            ctx.update({'use_domain': ('use_picking', '=', True)})
            partner = (
                procurement.rule_id.partner_address_id or (
                    procurement.group_id and procurement.group_id.partner_id)
            )
            company = (procurement.warehouse_id.company_id or
                       procurement.company_id)
            kwargs = {
                'partner_id': partner.id,
                'product_id': procurement.product_id.id,
                'partner_invoice_id':  partner.id,
                # TODO: Implement fuction to compute partner invoice id
                'partner_shipping_id': partner.id,
                'fiscal_category_id': (
                    procurement.rule_id.fiscal_category_id.id
                ),
                'company_id': company.id,
                'context': ctx,
            }

            obj_fp_rule = self.env['account.fiscal.position.rule']
            product_fc_id = obj_fp_rule.with_context(
                ctx).product_fiscal_category_map(
                    kwargs.get('product_id'),
                    kwargs.get('fiscal_category_id'),
                    partner.state_id.id)

            if product_fc_id:
                kwargs['fiscal_category_id'] = product_fc_id
                result['fiscal_category_id'] = product_fc_id
            else:
                result['fiscal_category_id'] = kwargs.get(
                    'fiscal_category_id')

            result_fr = obj_fp_rule.with_context(ctx).apply_fiscal_mapping(
                {'value': {}}, **kwargs)

            result.update({
                'fiscal_position': result_fr['value']['fiscal_position']})
        return result
