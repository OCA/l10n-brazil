# Copyright (C) 2014  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

# from openerp import models, api
#
#
# class ProcurementOrder(models.Model):
#     _inherit = "procurement.order"
#
#     @api.model
#     def _run_move_create(self, procurement):
#         result = super(ProcurementOrder, self)._run_move_create(procurement)
#         if procurement.sale_line_id:
#             result.update({
#                 'fiscal_category_id': (procurement
#                                        .sale_line_id.fiscal_category_id.id),
#                 'fiscal_position': procurement.sale_line_id.fiscal_position.id,
#             })
#         return result
