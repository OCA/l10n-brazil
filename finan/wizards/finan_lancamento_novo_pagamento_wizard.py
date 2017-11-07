# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinanLancamento(models.TransientModel):
    _name = b'finan.lancamento.wizard'
    _inherit = 'finan.lancamento'

    @api.multi
    def create_lancamento(self):
        vals = {
            'currency_id': self.currency_id.id or False,
            'currency_aliquota_id"': self.currency_aliquota_id.id or False,
            'tipo': self.tipo,
            'conta_id': self.conta_id.id,
            'empresa_id': self.empresa_id.id,
            'participante_id': self.participante_id.id,
            'divida_id': self.divida_id.id,
            'forma_pagamento_id': self.forma_pagamento_id.id or False,
            'exige_numero': self.exige_numero,
            'documento_id': self.documento_id.id or False,
            'numero': self.numero,
            'data_pagamento': self.data_pagamento,
            'banco_id': self.banco_id.id,
            'data_credito_debito': self.data_credito_debito,
            'vr_movimentado': self.vr_movimentado,
            'vr_documento': self.vr_documento,
            'vr_juros': self.vr_juros,
            'vr_multa': self.vr_multa,
            'vr_adiantado': self.vr_adiantado,
            'vr_desconto': self.vr_desconto,
            'vr_tarifas': self.vr_tarifas,
        }
        self.env['finan.lancamento'].create(vals)
        return {'type': 'ir.actions.act_window_close'}
