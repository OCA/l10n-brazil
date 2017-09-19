# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Transferência de Estoque',
        copy=False,
    )

    @api.multi
    def action_view_picking(self):
        action = \
            self.env.ref('stock.action_picking_tree_all').read()[0]

        if self.stock_picking_id:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = self.stock_picking_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def _confirma_estoque(self):
        self.ensure_one()
        #
        # Vamos concluir a entrega
        #
        if self.stock_picking_id:
            #
            # Leva o DANFE para o picking
            #
            if self.arquivo_pdf_id:
                pdf_anexo = self.arquivo_pdf_id
                nome_arquivo = pdf_anexo.datas_fname
                pdf = pdf_anexo.datas.decode('base64')
                self.stock_picking_id._grava_anexo(
                    nome_arquivo=nome_arquivo,
                    conteudo=pdf,
                    tipo='application/pdf',
                    model='stock.picking',
                )

            self.stock_picking_id.action_confirm()
            self.stock_picking_id.force_assign()

            #
            # Confirmando todas as saídas
            #
            for pack in self.stock_picking_id.pack_operation_ids:
                if pack.product_qty > 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()

            self.stock_picking_id.do_transfer()
            self.stock_picking_id.state = 'done'

    def _cancela_estoque(self):
        #
        # Vamos cancelar a venda?
        #
        if self.stock_picking_id:
            #
            # Leva o DANFE para o picking
            #
            if self.arquivo_pdf_id:
                pdf_anexo = self.arquivo_pdf_id
                nome_arquivo = pdf_anexo.datas_fname
                pdf = pdf_anexo.datas.decode('base64')
                self.stock_picking_id._grava_anexo(
                    nome_arquivo=nome_arquivo,
                    conteudo=pdf,
                    tipo='application/pdf',
                    model='stock.picking',
                )

            self.stock_picking_id.action_cancel()
            self.stock_picking_id.state = 'cancel'

    def executa_depois_autorizar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_autorizar()
        self._confirma_estoque()

    def executa_depois_cancelar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_cancelar()
        self._cancela_estoque()

    def executa_depois_denegar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_denegar()
        self._cancela_estoque()

    #@api.multi
    #def action_relacionar_picking(self):
        #for record in self:
            #if not record.stock_picking_id:
                #related_picking = self.env['stock.picking'].search(
                    #[('documento_id', '=', record.id)]
                #)
                #if related_picking:
                    #record.stock_picking_id = related_picking
                #else:
                    #record._action_criar_picking()

    #@api.multi
    #def _action_criar_picking(self):
        #for record in self:
            #vals = {}
            #vals = record._monta_dados_picking()
            #picking = self.env['stock.picking'].create(vals)
            #return picking

    #def _get_valor(self, record, campo):
        #valor = getattr(record, campo)
        #if hasattr(valor, 'ids'):
            #valor =  valor.ids

        #return valor

    #def _monta_dados_picking(self):
        #vals = {}
        ## Dados comuns ao stock_picking e o sped_documento
        #for field in self._fields:
            #if field in self.env['stock.picking']._fields and not field == 'id':
                #valor = self._get_valor(self, field)
                #vals.update({field: valor})

        ## Dados específicos do stock_picking
        #vals.update(self._get_campos_picking(self.operacao_id))

        ## Dados do stock_move
        #vals.update({'move_lines': []})
        #for item in self.item_ids:
            #move_line = {}
            #for field in self.item_ids._fields:
                #if field in self.env['stock.move']._fields and not \
                                #field == 'id':
                    #valor = self._get_valor(item, field)
                    #move_line.update({field: valor})
            #vals['move_lines'].append((0, 0, move_line))

        #return vals

    #def _get_campos_picking(self, operacao):
        #customer_loc, supplier_loc = self.env[
            #'stock.warehouse']._get_partner_locations()

        #location_dest_id = customer_loc if \
            #self.entrada_saida == '1' else supplier_loc

        #location_src_id = customer_loc if \
            #self.entrada_saida == '0' else supplier_loc

        #return {
            #'picking_type_id': operacao.stock_picking_type_id.id,
            #'warehouse_id': operacao.stock_picking_type_id.warehouse_id.id,
            #'location_id':
                #operacao.stock_picking_type_id.default_location_src_id.id or
                #location_src_id.id,
            #'location_dest_id':
                #operacao.stock_picking_type_id.default_location_dest_id.id or
                #location_dest_id.id,
        #}
