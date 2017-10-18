# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning as UserError
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime, hoje

except (ImportError, IOError) as err:
    _logger.debug(err)


class FinanLancamento(models.TransientModel):
    _name = b'finan.lancamento.wizard'
    _inherit = b'finan.lancamento'


    @api.multi
    def create_lancamento(self):
        vals = {
            'currency_id': self.currency_id.id or False,
            'currency_aliquota_id"': self.currency_aliquota_id.id or False,
            'tipo': self.tipo or False,
            'nome': self.nome or False,
            'situacao_divida_simples': self.situacao_divida_simples or False,
            'situacao_divida': self.situacao_divida or False,
            'conta_id': self.conta_id.id or False,
            'cnpj_cpf': self.cnpj_cpf or False,
            'cnpj_cpf_raiz': self.cnpj_cpf_raiz or False,
            'empresa_id': self.empresa_id.id or False,
            'participante_id': self.participante_id.id or False,
            'divida_id': self.divida_id.id or False,
            'forma_pagamento_id': self.forma_pagamento_id.id or False,
            'exige_numero': self.exige_numero or False,
            'documento_id': self.documento_id.id or False,
            'numero': self.numero or False,
            'data_pagamento': self.data_pagamento or False,
            'banco_id': self.banco_id.id or False,
            'data_credito_debito': self.data_credito_debito or False,
            'vr_documento': self.vr_documento or False,
            'vr_juros': self.vr_juros or False,
            'vr_multa': self.vr_multa or False,
            'vr_adiantado': self.vr_adiantado or False,
            'vr_desconto': self.vr_desconto or False,
            'vr_tarifas': self.vr_tarifas or False,
            'vr_total': self.vr_total or False
        }
        self.env['finan.lancamento'].create(vals)
        return {'type': 'ir.actions.act_window_close'}
