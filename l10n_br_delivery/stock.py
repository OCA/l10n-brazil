# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm, fields


class StockPicking(orm.Model):
    _inherit = 'stock.picking'
    _columns = {
        'vehicle_id': fields.many2one(
            'l10n_br_delivery.carrier.vehicle', u'Veículo'),
        'incoterm': fields.many2one(
            'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")}

    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        #TODO: Calcular o valor correto em caso de alteração da quantidade
        return None

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line,
                              invoice_id, invoice_vals, context=None):
        result = super(stock_picking, self)._prepare_invoice_line(
            cr, uid, group, picking, move_line, invoice_id, invoice_vals,
            context)
        #TODO: Calcular o valor correto em caso de alteração da quantidade
        result['insurance_value'] = move_line.sale_line_id.insurance_value
        result['other_costs_value'] = move_line.sale_line_id.other_costs_value
        result['freight_value'] = move_line.sale_line_id.freight_value
        return result



    def _invoice_hook(self, cr, uid, picking, invoice_id):
        """Call after the creation of the invoice."""        context = {}

        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.pool.get('res.company').browse(
            cr, uid, user.company_id.id, context=context)
        inv = self.pool.get("account.invoice").browse(cr,uid,invoice_id)
        vals = [
            ('Frete', company.account_freight_id, inv.amount_freight),
            ('Seguro', company.account_insurance_id, inv.amount_insurance),
            ('Outros Custos',company.account_other_costs, inv.amount_costs)
            ]

        ait_obj = self.pool.get('account.invoice.tax')
        for tax in vals:
            if tax[2] > 0:
                ait_obj.create(cr, uid,
                {
                 'invoice_id': invoice_id,
                 'name': tax[0],
                 'account_id': tax[1].id,
                 'amount': tax[2],
                 'base': tax[2],
                 'manual': 1,
                 'company_id': company.id,
                }, context=context)

        
        self.pool.get('account.invoice').write(
            cr, uid, invoice_id, {
                'partner_shipping_id': picking.partner_id.id,
                'carrier_id': picking.carrier_id and picking.carrier_id.id,
                'vehicle_id': picking.vehicle_id and picking.vehicle_id.id,
                'incoterm': picking.incoterm.id,
                'weight': picking.weight,
                'weight_net': picking.weight_net,
                'number_of_packages': picking.number_of_packages})

        return super(StockPicking, self)._invoice_hook(
            cr, uid, picking, invoice_id)


class StockPickingIn(orm.Model):
    _inherit = 'stock.picking.in'
    _columns = {
        'vehicle_id': fields.many2one(
            'l10n_br_delivery.carrier.vehicle', u'Veículo'),
        'incoterm': fields.many2one(
            'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")}


class StockPickingOut(orm.Model):
    _inherit = 'stock.picking.out'
    _columns = {
        'vehicle_id': fields.many2one(
            'l10n_br_delivery.carrier.vehicle', u'Veículo'),
        'incoterm': fields.many2one(
            'stock.incoterms', 'Tipo do Frete',
        help="Incoterm which stands for 'International Commercial terms"
        "implies its a series of sales terms which are used in the "
        "commercial transaction.")}
