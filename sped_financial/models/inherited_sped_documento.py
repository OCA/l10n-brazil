# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.addons.financial.constants import FINANCIAL_DEBT_2RECEIVE


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    financial_document_type_id = fields.Many2one(
        comodel_name='financial.document.type',
        string='Tipo de documento',
        ondelete='restrict',
    )
    financial_account_id = fields.Many2one(
        comodel_name='financial.account',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('type', '=', 'A')],
    )
    financial_move_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='documento_id',
        string='Lançamentos Financeiros',
        copy=False,
    )

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        res = super(SpedDocumento, self)._onchange_operacao_id()

        if not self.operacao_id:
            return res

        if self.operacao_id.financial_document_type_id:
            res['value']['financial_document_type_id'] = \
                self.operacao_id.financial_document_type_id.id

        if self.operacao_id.financial_account_id:
            res['value']['financial_account_id'] = \
                self.operacao_id.financial_account_id.id

        return res

    def gera_financial_move(self):
        """ Cria o lançamento financeiro do documento fiscal
        :return:
        """
        for documento in self:
            if documento.situacao_fiscal not in \
                    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO:
                # documento.apaga_financial_move()
                continue

            if documento.emissao == TIPO_EMISSAO_PROPRIA and \
                documento.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                continue

            #
            # Temporariamente, apagamos todos os lançamentos anteriores
            #
            self.financial_move_ids.unlink()

            for duplicata in self.duplicata_ids:
                dados = duplicata.prepara_financial_move()
                financial_move = \
                    self.env['financial.move'].create(dados)
                financial_move.action_confirm()

    def executa_depois_autorizar(self):
        super(SpedDocumento, self).executa_depois_autorizar()
        self.gera_financial_move()
