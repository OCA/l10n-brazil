# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    forma_pagamento_id = fields.Many2one(
        comodel_name='finan.forma.pagamento',
        string='Forma de pagamento',
        required=True,
        index=True,
    )

    @api.onchange('forma_pagamento_id')
    def _onchange_forma_pagamento_id(self):
        for condicao in self:
            if not condicao.forma_pagamento_id:
                continue

            forma_pagamento = condicao.forma_pagamento_id
            condicao.forma_pagamento = forma_pagamento.forma_pagamento
            condicao.bandeira_cartao = forma_pagamento.bandeira_cartao
            condicao.integracao_cartao = forma_pagamento.integracao_cartao

            if forma_pagamento.participante_id:
                condicao.participante_id = \
                    forma_pagamento.participante_id
            else:
                condicao.participante_id = False
