# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..constants.payment import (
    BANDEIRA_CARTAO_DICT,
    FORMA_PAGAMENTO_DICT,
    FORMA_PAGAMENTO_CARTOES,
    FORMA_PAGAMENTO_CARTAO_CREDITO,
    FORMA_PAGAMENTO_CARTAO_DEBITO,
)


class FiscalPaymentCondition(models.Model):
    _name = 'l10n_br_fiscal.payment.condition'
    _inherit = 'l10n_br_fiscal.payment.term.abstract'
    _description = 'Condição de Pagamento'
    _order = 'sequence, name'

    @api.depends('payment_mode_id', 'payment_term_id', 'bandeira_cartao')
    def _compute_name(self):
        for record in self:
            display_name = ''
            if record.payment_mode_id.forma_pagamento in FORMA_PAGAMENTO_CARTOES:
                if record.payment_mode_id.forma_pagamento == \
                        FORMA_PAGAMENTO_CARTAO_CREDITO:
                    display_name += '[Crédito '
                elif record.payment_mode_id.forma_pagamento == \
                        FORMA_PAGAMENTO_CARTAO_DEBITO:
                    display_name += '[Débito '
                if record.bandeira_cartao:
                    display_name += \
                        BANDEIRA_CARTAO_DICT[record.bandeira_cartao]
                display_name += '] '

            elif record.payment_mode_id.forma_pagamento:
                display_name += '['
                display_name += \
                    FORMA_PAGAMENTO_DICT[record.payment_mode_id.forma_pagamento]
                display_name += '] '

            display_name += record.payment_term_id.name

            record.name = display_name

    name = fields.Char(
        string="Name",
        compute='_compute_name',
        store=True,
        index=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        index=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        index=True,
    )
    payment_term_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.term',
        string='Payment Term',
        index=True,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.payment.mode',
        string='Payment Mode',
        index=True,
    )
    forma_pagamento = fields.Selection(
        related='payment_mode_id.forma_pagamento',
        store=True,
    )
