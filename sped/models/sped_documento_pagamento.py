# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo.addons.l10n_br_base.constante_tributaria import (
    FORMA_PAGAMENTO,
    BANDEIRA_CARTAO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
)

_logger = logging.getLogger(__name__)

try:
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedDocumentoPagamento(SpedBase, models.Model):
    _name = b'sped.documento.pagamento'
    _description = 'Pagamentos do Documento Fiscal'
    _order = 'documento_id, sequence, condicao_pagamento_id'
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
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )
    valor = fields.Monetary(
        string='Valor',
    )
    # Deprecado, utilizar o campo vr_troco do sped.documento
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
        comodel_name='sped.participante',
        string='Operadora do cartão',
        ondelete='restrict',
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
    )

    @api.onchange('condicao_pagamento_id', 'valor', 'documento_id',
                  'duplicata_ids')
    def _onchange_condicao_pagamento_id(self):
        res = {}
        valores = {}

        if not self.documento_id:
            self.documento_id = self.env['sped.documento'].browse(
                self.env.context.get('active_id', False)
            )

        res['value'] = valores

        if not (self.condicao_pagamento_id and self.documento_id):
            return res

        valor = D(self.valor or 0)

        duplicata_ids = self.condicao_pagamento_id.gera_parcela_ids(
            valor, self.documento_id.data_emissao
        )
        valores['duplicata_ids'] = duplicata_ids
        valores['forma_pagamento'] = self.condicao_pagamento_id.forma_pagamento
        valores['bandeira_cartao'] = self.condicao_pagamento_id.bandeira_cartao
        valores['integracao_cartao'] = \
            self.condicao_pagamento_id.integracao_cartao

        if self.condicao_pagamento_id.participante_id:
            valores['participante_id'] = \
                self.condicao_pagamento_id.participante_id.id
            valores['cnpj_cpf'] = \
                self.condicao_pagamento_id.participante_id.cnpj_cpf
        else:
            valores['participante_id'] = False
            valores['cnpj_cpf'] = False

        return res
