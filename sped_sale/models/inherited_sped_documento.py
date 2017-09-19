# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Pedido de Venda',
        ondelete='restrict',
        copy=False,
    )

    @api.multi
    def action_view_sale(self):
        action = \
            self.env.ref('sped_sale.sale_order_orcamento_action').read()[0]

        if self.sale_order_id:
            action['views'] = [
                (self.env.ref('sped_sale.sale_order_form').id, 'form')]
            action['res_id'] = self.sale_order_id.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def executa_depois_autorizar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_autorizar()
        #
        # Vamos concluir a venda
        #
        if self.sale_order_id:
            #
            # Leva o DANFE para a venda
            #
            if self.arquivo_pdf_id:
                pdf_anexo = self.arquivo_pdf_id
                nome_arquivo = pdf_anexo.datas_fname
                pdf = pdf_anexo.datas.decode('base64')
                self.sale_order_id._grava_anexo(
                    nome_arquivo=nome_arquivo,
                    conteudo=pdf,
                    tipo='application/pdf',
                    model='sale.order',
                )
            self.sale_order_id.state = 'done'

        self._confirma_estoque()

    def executa_depois_cancelar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_cancelar()
        #
        # Vamos cancelar a venda?
        #
        if self.sale_order_id:
            #
            # Leva o DANFE para a venda
            #
            if self.arquivo_pdf_id:
                pdf_anexo = self.arquivo_pdf_id
                nome_arquivo = pdf_anexo.datas_fname
                pdf = pdf_anexo.datas.decode('base64')
                self.sale_order_id._grava_anexo(
                    nome_arquivo=nome_arquivo,
                    conteudo=pdf,
                    tipo='application/pdf',
                    model='sale.order',
                )
            self.sale_order_id.state = 'cancel'
        self._cancela_estoque()

    def executa_depois_denegar(self):
        self.ensure_one()
        super(SpedDocumento, self).executa_depois_denegar()
        #
        # Vamos cancelar a venda?
        #
        if self.sale_order_id:
            #
            # Leva o DANFE para a venda
            #
            if self.arquivo_pdf_id:
                pdf_anexo = self.arquivo_pdf_id
                nome_arquivo = pdf_anexo.datas_fname
                pdf = pdf_anexo.datas.decode('base64')
                self.sale_order_id._grava_anexo(
                    nome_arquivo=nome_arquivo,
                    conteudo=pdf,
                    tipo='application/pdf',
                    model='sale.order',
                )
            self.sale_order_id.state = 'cancel'
        self._cancela_estoque()


    def _check_permite_alteracao(self, operacao='create', dados={},
                                 campos_proibidos=[]):
        CAMPOS_PERMITIDOS = [
            'stock_picking_id',
        ]
        for documento in self:
            if documento.modelo not in (MODELO_FISCAL_NFE,
                                        MODELO_FISCAL_NFCE):
                super(SpedDocumento, documento)._check_permite_alteracao(
                    operacao,
                    dados,
                )
                continue

            if documento.emissao != TIPO_EMISSAO_PROPRIA:
                super(SpedDocumento, documento)._check_permite_alteracao(
                    operacao,
                    dados,
                )
                continue

            if documento.permite_alteracao:
                continue

            permite_alteracao = False
            #
            # Trata alguns campos que é permitido alterar depois da nota
            # autorizada
            #
            if documento.situacao_nfe == SITUACAO_NFE_AUTORIZADA:
                for campo in dados:
                    if campo in CAMPOS_PERMITIDOS:
                        permite_alteracao = True
                        break
                    elif campo not in campos_proibidos:
                        campos_proibidos.append(campo)

            if permite_alteracao:
                continue

            super(SpedDocumento, documento)._check_permite_alteracao(
                operacao,
                dados,
                campos_proibidos
            )
