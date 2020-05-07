# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.payment import (
    BANDEIRA_CARTAO,
    BANDEIRA_CARTAO_DICT,
    FORMA_PAGAMENTO,
    FORMA_PAGAMENTO_DICT,
    INTEGRACAO_CARTAO,
    INTEGRACAO_CARTAO_NAO_INTEGRADO,
    FORMA_PAGAMENTO_CARTOES,
    FORMA_PAGAMENTO_CARTAO_CREDITO,
    FORMA_PAGAMENTO_CARTAO_DEBITO,
    FORMA_PAGAMENTO_OUTROS,
)


class FiscalPaymentTermAbstract(models.AbstractModel):
    _name = 'l10n_br_fiscal.payment.term.abstract'
    _description = 'Campos dos Pagamentos Brasileiros'
    _rec_name = 'display_name'

    display_name = fields.Char(
        compute='_compute_display_name2', store=True, index=True)

    forma_pagamento = fields.Selection(
        selection=FORMA_PAGAMENTO,
        string='Forma de pagamento',
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
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Operadora do cartão',
        ondelete='restrict',
    )

    @api.depends('name', 'forma_pagamento', 'bandeira_cartao')
    def _compute_display_name2(self):

        for payment_term in self:
            display_name = ''
            if payment_term.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                if payment_term.forma_pagamento == FORMA_PAGAMENTO_CARTAO_CREDITO:
                    display_name += '[Crédito '
                elif payment_term.forma_pagamento == FORMA_PAGAMENTO_CARTAO_DEBITO:
                    display_name += '[Débito '
                if payment_term.bandeira_cartao:
                    display_name += \
                        BANDEIRA_CARTAO_DICT[payment_term.bandeira_cartao]
                display_name += '] '

            elif payment_term.forma_pagamento:
                display_name += '['
                display_name += \
                    FORMA_PAGAMENTO_DICT[payment_term.forma_pagamento]
                display_name += '] '

            display_name += payment_term.name

            payment_term.display_name = display_name
