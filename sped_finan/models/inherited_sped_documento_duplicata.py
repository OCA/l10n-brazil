# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models
from odoo.addons.finan.constantes import FINAN_DIVIDA_A_RECEBER, \
    FINAN_DIVIDA_A_PAGAR
from odoo.addons.l10n_br_base.constante_tributaria import TIPO_EMISSAO_PROPRIA
from odoo.exceptions import ValidationError


class SpedDocumentoDuplicata(models.Model):
    _inherit = 'sped.documento.duplicata'

    finan_lancamento_ids = fields.One2many(
        comodel_name='finan.lancamento',
        inverse_name='sped_documento_duplicata_id',
        string='Lançamentos Financeiros',
        copy=False
    )

    def prepara_finan_lancamento(self):
        dados = {
            'data_documento': self.documento_id.data_emissao,
            'participante_id': self.documento_id.participante_id.id,
            'empresa_id': self.documento_id.empresa_id.id,
            'referencia_id': 'sped.documento,' + str(self.documento_id.id),
            'sped_documento_id': self.documento_id.id,
            'sped_documento_duplicata_id': self.id,
            'documento_id': \
                self.documento_id.finan_documento_id.id,
            'conta_id': self.documento_id.finan_conta_id.id,
            'data_vencimento': self.data_vencimento,
            'vr_documento': self.valor,
            'numero':
                '{0.serie}-{0.numero:0.0f}-{1.numero}/{2}'.format(
                    self.documento_id, self,
                    len(self.documento_id.duplicata_ids)),
        }

        if self.documento_id.condicao_pagamento_id.forma_pagamento_id:
            dados['forma_pagamento_id'] = \
                self.documento_id.condicao_pagamento_id.forma_pagamento_id.id

        # Informações da carteira para emissao do boleto automatico
        if self.documento_id.carteira_id:
            dados['carteira_id'] = self.documento_id.carteira_id.id
            dados['banco_id'] = self.documento_id.carteira_id.banco_id.id

        if self.documento_id.emissao == TIPO_EMISSAO_PROPRIA:
            dados['tipo'] = FINAN_DIVIDA_A_RECEBER
        else:
            dados['tipo'] = FINAN_DIVIDA_A_PAGAR

        return dados

    def gera_lancamento_financeiro(self):
        for duplicata in self:
            dados = duplicata.prepara_finan_lancamento()
            finan_lancamento_id = self.env['finan.lancamento'].create(dados)
