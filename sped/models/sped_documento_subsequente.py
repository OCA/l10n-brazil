# -*- coding: utf-8 -*-
#
# Copyright 2018 KMEE INFORMATICA LTDA
#   Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import *

SITUACAO_SUBSEQUENTE = (
    ('manual', 'Manualmente'),
    ('nota_de_cupom', 'Gerar Nota Fiscal de Cupons Fiscais'),
    ('nota_de_remessa', 'Gerar Nota Fiscal de Remessa'),
)


class SpedDocumentoSubsequente(models.Model):
    _name = b'sped.documento.subsequente'
    _description = 'Sped Documento Subsequente'

    documento_origem_id = fields.Many2one(
        string='Documento de origem',
        comodel_name='sped.documento',
        required=True,
        ondelete='cascade',
    )

    operacao_subsequente_id = fields.Many2one(
        string='Operação subsequente',
        comodel_name='sped.operacao.subsequente',
        required=True,
    )

    sped_operacao_id = fields.Many2one(
        string='Operação relacionada',
        comodel_name='sped.operacao',
        required=True,
    )

    documento_subsequente_id = fields.Many2one(
        string='Documento subsequente',
        comodel_name='sped.documento',
        ondelete='set null',
    )

    operacao_realizada = fields.Boolean(
        string='Operação Realizada',
        compute='_compute_operacao_realizada',
        default=False,
    )

    def _subsequente_tipo_pagamento(self):
        return (self.sped_operacao_id.ind_forma_pagamento or
                self.documento_origem_id.ind_forma_pagamento)

    def _subsequente_condicao_pagamento(self):
        return (self.sped_operacao_id.condicao_pagamento_id or
                self.documento_origem_id.condicao_pagamento_id)

    def _subsequente_empresa(self):
        return (self.sped_operacao_id.empresa_id or
                self.documento_origem_id.empresa_id)

    def _subsequente_participante(self):
        return (self.operacao_subsequente_id.participante_id or
                self.documento_origem_id.participante_id)

    def _subsequente_referenciado(self):
        if self.operacao_subsequente_id.referenciar_documento:
            return self.env.context.get(
                'referenciado_ids',
                self.documento_origem_id._prepare_subsequente_referenciado()
            )
        return []

    def gera_documento_subsequente(self):
        self._gera_documento_subsequente()

    def _gera_documento_subsequente(self):
        if self.operacao_realizada:
            return self.documento_subsequente_id

        novo_doc = self.documento_origem_id.copy()

        novo_doc.participante_id = self._subsequente_participante()
        novo_doc.empresa_id = self._subsequente_empresa()
        novo_doc.operacao_id = self.sped_operacao_id
        novo_doc.condicao_pagamento_id = \
            self._subsequente_condicao_pagamento()
        novo_doc.tipo_pagamento = self._subsequente_tipo_pagamento()

        #
        # Referenciar documento
        #
        referencia_ids = self._subsequente_referenciado()
        novo_doc._referencia_documento(referencia_ids)

        documento = novo_doc.gera_documento()
        documento.situacao_nfe = SITUACAO_NFE_A_ENVIAR
        documento.numero = False
        documento.data_entrada_saida = False
        self.documento_subsequente_id = documento

    @api.depends('documento_subsequente_id.situacao_nfe')
    def _compute_operacao_realizada(self):
        for subsequente in self:
            if not subsequente.documento_subsequente_id:
                continue
            if subsequente.documento_subsequente_id.situacao_nfe == \
                    SITUACAO_NFE_CANCELADA:
                subsequente.operacao_realizada = False
            else:
                subsequente.operacao_realizada = True

    @api.multi
    def ver_documento_subsequente(self):
        return {
            'name': 'Documento Subsequente',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'views': [[False, 'form']],
            'res_model': 'sped.documento',
            'domain': [['id', 'in', [self.documento_subsequente_id.id]]],
            'res_id': self.documento_subsequente_id.id,
        }

    @api.multi
    def ver_documento_origem(self):
        return {
            'name': 'Documento de Origem',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'views': [[False, 'form']],
            'res_model': 'sped.documento',
            'domain': [['id', 'in', [self.documento_origem_id.id]]],
            'res_id': self.documento_origem_id.id,
        }

    @api.multi
    def unlink(self):
        for subsequente_id in self:
            if subsequente_id.operacao_realizada:
                raise UserWarning("Não é possível excluir o documento: o "
                                  "documento subsequente já foi gerado.")
        return super(SpedDocumentoSubsequente, self).unlink()



    @api.multi
    def _confirma_geracao_documento(self):
        """ Verificamos se podemos gerar o documento subsequente
        :return: True permitindo a geração
        """
        result = False

        if self.operacao_subsequente_id.situacao_geracao in \
                [x for x, y in SITUACAO_SUBSEQUENTE]:
            cupom = self.documento_origem_id.filtered(
                lambda documento: documento.modelo in (
                    MODELO_FISCAL_CFE,
                    MODELO_FISCAL_NFCE,
                    MODELO_FISCAL_CUPOM_FISCAL_ECF,))
            if cupom and self.operacao_subsequente_id.situacao_geracao == \
                    'nota_de_cupom':
                result = True
            elif self.operacao_subsequente_id.situacao_geracao == \
                    'manual' and self.env.context.get('manual', False):
                result = True
            elif self.operacao_subsequente_id.situacao_geracao == \
                    'nota_de_remessa':
                result = True
        elif self.documento_origem_id.situacao_nfe == \
                self.operacao_subsequente_id.situacao_geracao:
            result = True
        return result
