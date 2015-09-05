# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
# Copyright (C) 2012  Raphaël Valyi - Akretion                                #
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

from openerp.osv import orm


class StockPicking(orm.Model):
    _inherit = 'stock.picking'

    # def _prepare_invoice(self, cr, uid, picking, partner,
    #                     inv_type, journal_id, context=None):
    #     result = super(StockPicking, self)._prepare_invoice(
    #         cr, uid, picking, partner, inv_type, journal_id, context)
    #
    #     fp_comment = []
    #     fc_comment = []
    #     fp_ids = []
    #     fc_ids = []
    #
    #     if picking.fiscal_position and \
    #     picking.fiscal_position.inv_copy_note and \
    #     picking.fiscal_position.note:
    #         fp_comment.append(picking.fiscal_position.note)
    #
    #     for move in picking.move_lines:
    #         if move.sale_line_id:
    #             line = move.sale_line_id
    #             if line.fiscal_position and \
    #             line.fiscal_position.inv_copy_note and \
    #             line.fiscal_position.note:
    #                 if not line.fiscal_position.id in fp_ids:
    #                     fp_comment.append(line.fiscal_position.note)
    #                     fp_ids.append(line.fiscal_position.id)
    #
    #         if move.product_id.ncm_id:
    #             fc = move.product_id.ncm_id
    #             if fc.inv_copy_note and fc.note:
    #                 if not fc.id in fc_ids:
    #                     fc_comment.append(fc.note)
    #                     fc_ids.append(fc.id)
    #
    #     result['comment'] = " - ".join(fp_comment + fc_comment)
    #     result['fiscal_category_id'] = picking.fiscal_category_id and \
    #     picking.fiscal_category_id.id
    #     result['fiscal_position'] = picking.fiscal_position and \
    #     picking.fiscal_position.id
    #     return result

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move,
                          context=None):
        """
        Preenche os dados da invoice com dados da sale order, seria possivel
        preencher os dados da invoice carregando os dados da sale order para
        o procurement e em seguida para o stock.picking e stock.move.

        Esta abordagem pode ser feita sobrescrevendo os metodos:
         1. Criar devidos campos no procurement
         2. Sobrescrever _prepare_oder_line_procurement
         3. Sobrescrever _run_move_create

        Ainda não encontrei necessidade funcional que precise desse
        requisito. É interessante manter a invoice coerente com a sale.order
        e não permitir a alteração dos campos fiscais.
        """
        sale = move.picking_id.sale_id
        if sale and not journal_id:
            journal_id = sale.fiscal_category_id.property_journal.id
        inv_vals = super(StockPicking, self)._get_invoice_vals(
            cr, uid, key, inv_type, journal_id, move, context=context)
        if sale:
            inv_vals.update({
                'comment': sale.note, # TODO: Verificar se os comentarios estão
                #  ok!
                'fiscal_category_id': (sale.fiscal_category_id and
                                       sale.fiscal_category_id.id),
                'fiscal_position': (sale.fiscal_position and
                                    sale.fiscal_position.id),
                'ind_pres': sale.ind_pres,
                })
        return inv_vals

class StockMove(orm.Model):
    _inherit = 'stock.move'
    
    def _prepare_picking_assign(self, cr, uid, move, context=None):        
        result = super(StockMove, self)._prepare_picking_assign(cr, uid,
            move, context)
        result['fiscal_category_id'] = move.fiscal_category_id and \
            move.fiscal_category_id.id
        result['fiscal_position'] = move.fiscal_position and \
            move.fiscal_position.id             
        return result

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type,
                               context=None):
        res = super(StockMove, self)._get_invoice_line_vals(
            cr, uid, move, partner, inv_type, context=context)
        if move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id

            fiscal_position = sale_line.fiscal_position or \
                sale_line.order_id.fiscal_position or False
            fiscal_category_id = sale_line.fiscal_category_id or \
                sale_line.order_id.fiscal_category_id or False

            res.update({
                'cfop_id': (fiscal_position and fiscal_position.cfop_id and
                                fiscal_position.cfop_id.id),
                'fiscal_category_id': (fiscal_category_id and
                                       fiscal_category_id.id),
                'fiscal_position': fiscal_position and fiscal_position.id,
                'partner_id': sale_line.order_partner_id.id,
                'company_id': sale_line.company_id.id,
            })

        return res