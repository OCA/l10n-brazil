# Copyright (C) 2022-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains('move_type', 'journal_id')
    def _check_journal_type(self):
        # A implementação do modulo stock_picking_invoicing é justamente o caso
        # de ser preciso ter um Documento Fiscal mas não ser nem uma Venda nem
        # uma Compra é por exemplo uma Transferencia entre Filiais, Remessa para
        # Conserto e etc por padrão apenas os casos onde o campo Type do
        # account.journal são ou sale ou purchase permitem a criação da Invoice
        # por isso o metodo está sendo sobre escrito aqui.
        # TODO - isso deveria estar no modulo stock_picking_invoicing?
        for record in self:
            if record.picking_ids:
                inv_gen_from_picking = False
                pickings_name = record.picking_ids.mapped("name")
                list_invoice_origin = record.invoice_origin.split(", ")
                for picking_name in pickings_name:
                    if picking_name in list_invoice_origin:
                        picking = record.picking_ids.filtered(
                            lambda x: x.name == picking_name
                        )
                        # Se tiver um Pedido de Venda ou Compra relacionado
                        # deve ser feita a validação
                        has_sale_or_purchase = False
                        if hasattr(picking, "sale_id"):
                            if picking.sale_id:
                                has_sale_or_purchase = True
                        if hasattr(picking, "purchase_id"):
                            if picking.purchase_id:
                                has_sale_or_purchase = True

                        if has_sale_or_purchase:
                            continue

                        inv_gen_from_picking = True

                # Não deve ser validado porque foi gerado pelo stock.picking
                if inv_gen_from_picking:
                    return False

                return super()._check_journal_type()
