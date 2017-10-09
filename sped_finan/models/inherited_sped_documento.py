# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *
from odoo.addons.finan.constantes import FINAN_DIVIDA_A_RECEBER


class SpedDocumento(models.Model):
    _inherit = 'sped.documento'

    finan_documento_id = fields.Many2one(
        comodel_name='finan.documento',
        string='Tipo de documento',
        ondelete='restrict',
    )
    finan_conta_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta financeira',
        ondelete='restrict',
        domain=[('tipo', '=', 'A')],
    )
    finan_lancamento_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='sped_documento_id',
        string='Lançamentos Financeiros',
        copy=False,
    )

    @api.onchange('operacao_id', 'emissao', 'natureza_operacao_id')
    def _onchange_operacao_id(self):
        res = super(SpedDocumento, self)._onchange_operacao_id()

        if not self.operacao_id:
            return res

        if self.operacao_id.finan_documento_id:
            res['value']['finan_documento_id'] = \
                self.operacao_id.finan_documento_id.id

        if self.operacao_id.finan_conta_id:
            res['value']['finan_conta_id'] = \
                self.operacao_id.finan_conta_id.id

        return res

    def exclui_finan_lancamento(self):
        for documento in self:
            #
            # Para excluir os lançamentos vinculados à nota, precisamos
            # primeiro quebrar o vínculo de segurança
            #
            lancamentos = []

            for lancamento in documento.finan_lancamento_ids:
                lancamento.sped_documento_duplicata_id = False
                lancamento.sped_documento_id = False
                lancamento.referencia_id = False
                lancamentos.append(lancamento)

            for lancamento in lancamentos:
                lancamento.unlink()

    def gera_finan_lancamento(self):
        for documento in self:
            if documento.situacao_fiscal not in \
                    SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO:
                continue

            if documento.emissao == TIPO_EMISSAO_PROPRIA and \
                documento.entrada_saida == ENTRADA_SAIDA_ENTRADA:
                continue

            documento.duplicata_ids.gera_lancamento_financeiro()

    def regera_finan_lancamento(self):
        for documento in self:
            documento.exclui_finan_lancamento()
            documento.gera_finan_lancamento()

    def executa_depois_autorizar(self):
        super(SpedDocumento, self).executa_depois_autorizar()
        self.gera_finan_lancamento()

    def executa_depois_create(self):
        for documento in self:
            documento.gera_finan_lancamento()

    @api.model
    def create(self, dados):
        res = super(SpedDocumento, self).create(dados)
        res.executa_depois_create()
        return res

    def executa_antes_write(self):
        for documento in self:
            documento.exclui_finan_lancamento()

    def executa_depois_write(self):
        for documento in self:
            documento.gera_finan_lancamento()

    def write(self, dados):
        self.executa_antes_write()
        res = super(SpedDocumento, self).write(dados)
        self.executa_depois_write()
        return res

    def executa_antes_unlink(self):
        for documento in self:
            documento.exclui_finan_lancamento()

    def unlink(self):
        self.executa_antes_unlink()
        return super(SpedDocumento, self).unlink()
