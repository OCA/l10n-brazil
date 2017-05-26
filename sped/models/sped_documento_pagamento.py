# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.addons.l10n_br_base.constante_tributaria import (
    FORMA_PAGAMENTO,
    BANDEIRA_CARTAO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoPagamento(models.Model):
    _name = b'sped.documento.pagamento'
    _description = 'Pagamentos do Documento Fiscal'
    _inherit = 'sped.base'
    _order = 'documento_id, sequence, payment_term_id'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento',
        ondelete='cascade',
        required=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Forma de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
    valor = fields.Monetary(
        string='Valor',
    )
    troco = fields.Monetary(
        string='Troco',
    )
    autorizacao = fields.Char(
        string='Autorização nº',
        size=20,
    )
    duplicata_ids = fields.One2many(
        comodel_name='sped.documento.duplicata',
        inverse_name='pagamento_id',
        string='Duplicatas',
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string='Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string='Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    participante_id = fields.Many2one(
        string='Operadora do cartão',
        ondelete='restrict',
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
    )

    @api.onchange('payment_term_id', 'valor', 'documento_id', 'duplicata_ids')
    def _onchange_payment_term(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not (self.payment_term_id and self.valor and self.documento_id):
            return res

        valor = Decimal(self.valor or 0)

        #
        # Para a compatibilidade com a chamada original (super), que usa
        # o decorator deprecado api.one, pegamos aqui sempre o 1º elemento
        # da lista que vai ser retornada
        #
        lista_vencimentos = self.payment_term_id.compute(
            valor,
            self.documento_id.data_emissao,
        )[0]

        duplicata_ids = [
            [5, False, {}],
        ]

        parcela = 1
        for data_vencimento, valor in lista_vencimentos:
            duplicata = {
                'numero': str(parcela),
                'data_vencimento': data_vencimento,
                'valor': valor,
            }
            duplicata_ids.append([0, False, duplicata])
            parcela += 1

        valores['duplicata_ids'] = duplicata_ids
        valores['forma_pagamento'] = self.payment_term_id.forma_pagamento
        valores['bandeira_cartao'] = self.payment_term_id.bandeira_cartao
        valores['integracao_cartao'] = self.payment_term_id.integracao_cartao

        if self.payment_term_id.participante_id:
            valores['participante_id'] = \
                self.payment_term_id.participante_id.id
            valores['cnpj_cpf'] = \
                self.payment_term_id.participante_id.cnpj_cpf
        else:
            valores['participante_id'] = False
            valores['cnpj_cpf'] = False

        return res
