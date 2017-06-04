# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    TIPO_PRODUTO_SERVICO_SERVICOS,
    TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO,
)


class Documento(models.Model):
    _inherit = 'sped.documento'

    account_invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string=u'Invoice original',
        ondelete='restrict',
    )

    def prepare_sync_to_invoice(self):
        self.ensure_one()

        dados = {
            'name': self.nome,
            'default_code': self.codigo,
            'active': True,
            'weight': self.peso_liquido,
            'uom_id': self.unidade_id.uom_id.id,
            'uom_po_id': self.unidade_id.uom_id.id,
            'standard_price': self.preco_custo,
            'list_price': self.list_price,
            'sale_ok': True,
            'purchase_ok': True,
            'barcode': self.codigo_barras,
        }

        if self.tipo == TIPO_PRODUTO_SERVICO_SERVICOS:
            dados['type'] = 'service'

        elif self.tipo == TIPO_PRODUTO_SERVICO_MATERIAL_USO_CONSUMO:
            dados['type'] = 'consu'

        else:
            dados['type'] = 'product'

        return dados

    @api.multi
    def sync_to_invoice(self):
        #
        # TODO: trata exclusão de documento recebido, excluir o invoice
        # quando necessário
        #
        for documento in self:
            if not (documento.eh_venda or
                    documento.eh_compra or
                    documento.eh_devolucao_venda or
                    documento.eh_devolucao_compra):
                continue

                # if documento.state !=
                # 'autorizado' or documento.state != 'cancelado':
                # continue

            dados = documento.prepare_sync_to_invoice()

            if documento.account_invoice_id:
                documento.account_invoice_id.write(dados)
            else:
                account_invoice_id = self.env['account.invoice'].create(dados)
                documento.write({'account_invoice_id': account_invoice_id.id})

    @api.model
    def create(self, dados):
        documento = super(Documento, self).create(dados)
        # documento.sync_to_invoice()

        return documento

    @api.multi
    def write(self, dados):
        res = super(Documento, self).write(dados)
        # self.sync_to_invoice()

        return res

    @api.multi
    def unlink(self):
        res = super(Documento, self).unlink()
        # self.sync_to_invoice()

        return res
