# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants.payment import (
    BANDEIRA_CARTAO,
    FORMA_PAGAMENTO,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
    FORMA_PAGAMENTO_OUTROS,
)


class FiscalPaymentTermAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.payment.term.abstract'
    _description = 'Campos dos Pagamentos Brasileiros'

    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Tipo pagamento',
        default=FORMA_PAGAMENTO_OUTROS,
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
    partner_card_id = fields.Many2one(
        comodel_name='res.partner',
        string='Operadora do cartão',
        ondelete='restrict',
    )
    partner_card_cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        related='partner_card_id.cnpj_cpf',
        store=True,
        size=18,
    )
