# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from ..constantes import CAMPO_DOCUMENTO_FISCAL_ITEM


class SpedDocumentoItem(models.Model):
    _inherit = 'sped.documento.item'

    def gera_account_move_line(self, account_move, move_template, line_ids,
                               campos_jah_contabilizados=[]):
        for item in self:
            for template_item in move_template.item_ids:
                if not getattr(item, template_item.campo, False):
                    continue

                if template_item.campo in campos_jah_contabilizados:
                    continue

                #
                # Nas notas de entrada por compra ou devolução de venda, se
                # não se vai aproveitar o crédito do imposto, ele não é
                # contabilizado à parte
                #
                if item.documento_id.eh_compra or \
                        item.documento_id.eh_devolucao_venda:
                    if template_item.campo in ('vr_icms', 'vr_icms_sn') and \
                            not item.credita_icms:
                        continue
                    elif template_item.campo == 'vr_icms_st' and \
                            not item.credita_icms_st:
                        continue
                    elif template_item.campo == 'vr_ipi' and \
                            not item.credita_ipi:
                        continue
                    elif template_item.campo in ('vr_pis_proprio',
                                                 'vr_cofins_proprio') and not item.credita_pis_cofins:
                        continue

                dados = {
                    'move_id': account_move.id,
                    'sped_documento_item_id': item.id,
                    'name': item.produto_id.nome,
                    'narration': template_item.campo,
                    'debit': getattr(item, template_item.campo, 0),
                    'currency_id': item.currency_id.id,
                }

                account_debito_id = None
                if template_item.account_debito_id:
                    account_debito_id = template_item.account_debito_id
                elif template_item.campo in CAMPO_DOCUMENTO_FISCAL_ITEM:
                    if item.documento_id.eh_venda:
                        account_debito_id = \
                            item.produto_id.product_id.property_account_income_id
                    elif item.documento_id.eh_compra:
                        account_debito_id = \
                            item.produto_id.product_id.property_account_expense_id
                else:
                    if item.documento_id.eh_venda:
                        account_debito_id = item.documento_id.participante_id.partner_id.property_account_receivable_id
                    elif item.documento_id.eh_compra:
                        account_debito_id = item.documento_id.participante_id.partner_id.property_account_payable_id

                if account_debito_id is None:
                    # raise
                    pass
                else:
                    dados['account_id'] = account_debito_id.id

                line_ids.append([0, 0, dados])

                dados = {
                    'move_id': account_move.id,
                    'sped_documento_item_id': item.id,
                    'name': item.produto_id.nome,
                    'narration': template_item.campo,
                    'credit': getattr(item, template_item.campo, 0),
                    'currency_id': item.currency_id.id,
                }

                account_credito_id = None
                if template_item.account_credito_id:
                    account_credito_id = template_item.account_credito_id
                elif template_item.campo in CAMPO_DOCUMENTO_FISCAL_ITEM:
                    if item.documento_id.eh_venda:
                        account_credito_id = \
                            item.produto_id.product_id.property_account_income_id
                    elif item.documento_id.eh_compra:
                        account_credito_id = \
                            item.produto_id.product_id.property_account_expense_id
                else:
                    if item.documento_id.eh_venda:
                        account_credito_id = item.documento_id.participante_id.partner_id.property_account_receivable_id
                    elif item.documento_id.eh_compra:
                        account_credito_id = item.documento_id.participante_id.partner_id.property_account_payable_id

                if account_credito_id is None:
                    # raise
                    pass
                else:
                    dados['account_id'] = account_credito_id.id

                line_ids.append([0, 0, dados])
                campos_jah_contabilizados.append(template_item.campo)

        if move_template.parent_id:
            self.gera_account_move_line(account_move, move_template.parent_id,
                                        line_ids, campos_jah_contabilizados=campos_jah_contabilizados)

    @api.depends('modelo', 'emissao')
    def _compute_permite_alteracao(self):
        super(SpedDocumentoItem, self)._compute_permite_alteracao()

        for item in self:
            if not item.permite_alteracao:
                continue

            if not self.documento_id.permite_alteracao:
                item.permite_alteracao = False
