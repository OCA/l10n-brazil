# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models


class DocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    account_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string=u'Invoice line original',
        ondelete='restrict',
    )

    def prepare_sync_to_invoice_line(self):
        self.ensure_one()

        dados = {
            'name': self.codigo,
            # 'categ_id': categ_id,
            'active': True,
        }

        if not self.invoice_line_id:
            dados['invoice_line_type'] = 'bigger'
            dados['factor'] = 1
            dados['rounding'] = 0.01

        return dados

    @api.multi
    def sync_to_invoice_line(self):
        #
        # TODO: tratar aqui a exclusão do item da NF recebida, excluir o item
        # correspondente do invoice
        #
        for item in self:
            if not (item.documento_id.eh_venda or
                    item.documento_id.eh_compra or
                    item.documento_id.eh_devolucao_venda or
                    item.documento_id.eh_devolucao_compra):
                continue

            if (item.documento_id.state != 'autorizado' or
                    item.documento_id.state != 'cancelado'):
                continue

            dados = item.prepare_sync_to_invoice_line()
            item.invoice_line_id.write(dados)

    @api.model
    def create(self, dados):
        item = super(DocumentoItem, self).create(dados)
        item.sync_to_invoice_line()

        return item

    @api.multi
    def write(self, dados):
        res = super(DocumentoItem, self).write(dados)
        self.sync_to_invoice_line()

        return res

    @api.multi
    def unlink(self):
        res = super(DocumentoItem, self).unlink()
        self.sync_to_invoice_line()

        return res
