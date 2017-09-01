# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import TIPO_EMISSAO_PROPRIA
from odoo.addons.financial.constants import FINANCIAL_DEBT_2RECEIVE, \
    FINANCIAL_DEBT_2PAY


class SpedDocumentoDuplicata(models.Model):
    _inherit = 'sped.documento.duplicata'

    financial_move_ids = fields.One2many(
        comodel_name='financial.move',
        inverse_name='documento_duplicata_id',
        string='Lançamentos Financeiros',
        copy=False
    )

    def prepara_financial_move(self):
        dados = {
            'date_document': self.documento_id.data_emissao,
            'participante_id': self.documento_id.participante_id,
            'partner_id': self.documento_id.participante_id.partner_id.id,
            'empresa_id': self.documento_id.empresa_id.id,
            'company_id': self.documento_id.empresa_id.company_id.id,
            'doc_source_id': 'sped.documento,' + str(self.documento_id.id),
            'currency_id': self.documento_id.currency_id.id,
            'documento_id': self.documento_id.id,
            'documento_duplicata_id': self.id,
            'document_type_id': \
                self.documento_id.financial_document_type_id.id,
            'account_id': self.documento_id.financial_account_id.id,
            'date_maturity': self.data_vencimento,
            'amount_document': self.valor,
            'document_number':
                '{0.serie}-{0.numero:0.0f}-{1.numero}/{2}'.format(
                    self.documento_id, self,
                    len(self.documento_id.duplicata_ids)),
        }

        if self.documento_id.emissao == TIPO_EMISSAO_PROPRIA:
            dados['type'] = FINANCIAL_DEBT_2RECEIVE
        else:
            dados['type'] = FINANCIAL_DEBT_2PAY

        return dados
