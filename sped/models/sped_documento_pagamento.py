# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import api, fields, models
from ..constante_tributaria import *
import logging
_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal

except (ImportError, IOError) as err:
    _logger.debug(err)


class DocumentoPagamento(models.Model):
    _description = u'Pagamento do Documento Fiscal'
    _inherit = 'sped.base'
    _name = 'sped.documento.pagamento'
    _order = 'documento_id, sequence, payment_term_id'
    # _rec_name = 'numero'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento',
        ondelete='cascade',
        required=True,
    )
    sequence = fields.Integer(
        default=10,
    )
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term',
        string=u'Forma de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
    valor = fields.Monetary(
        string=u'Valor',
    )
    troco = fields.Monetary(
        string=u'Troco',
    )
    autorizacao = fields.Char(
        string=u'Autorização nº',
        size=20,
    )
    duplicata_ids = fields.One2many(
        comodel_name='sped.documento.duplicata',
        inverse_name='pagamento_id',
        string=u'Duplicatas',
    )
    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string=u'Forma de pagamento',
    )
    bandeira_cartao = fields.Selection(
        selection=BANDEIRA_CARTAO,
        string=u'Bandeira do cartão',
    )
    integracao_cartao = fields.Selection(
        selection=INTEGRACAO_CARTAO,
        string=u'Integração do cartão',
        default=INTEGRACAO_CARTAO_NAO_INTEGRADO,
    )
    participante_id = fields.Many2one(
        string=u'Operadora do cartão',
        ondelete='restrict',
    )
    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
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

        lista_vencimentos = self.payment_term_id.compute(
            valor,
            self.documento_id.data_emissao,
        )

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
