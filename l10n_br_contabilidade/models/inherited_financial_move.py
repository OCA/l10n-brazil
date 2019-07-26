# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
from openerp.exceptions import Warning as UserError


class FinancialMove(models.Model):
    _inherit = b'financial.move'
    _description = 'Financial Move'

    name = fields.Char(
        string='Financial Reference',
        compute='_compute_display_name',
    )

    account_event_id = fields.Many2one(
        string=u'Evento Contábil',
        comodel_name='account.event',
        copy=False,
    )

    @api.multi
    def action_confirm(self):
        for record in self:
            record.change_state('open')

    @api.multi
    def create_account_move(self):
        """
        Por conta da geração do evento contábil para amarrar a contabilidade
        com o financeiro, foi necessário herdar esta função e sobre escrever
        de modo que ela fique inativa.
        :return:
        """
        pass

    def get_dicionario_evento_contabil(
            self, data_pagamento, linhas_evento):
        vals = {
            'ref': 'Financeiro - {}'.format(self.doc_source_id.name),
            'origem': '{},{}'.format('financial.move', self.id),
            'data': data_pagamento,
            'account_event_line_ids': linhas_evento,
        }

        return vals

    @api.multi
    def gerar_evento_contabil(self, data_pagamento=False):
        for record in self:
            linhas_evento = record.doc_source_id.get_linhas_evento_contabeis(
                record.amount_total)
            vals = record.get_dicionario_evento_contabil(
                data_pagamento, linhas_evento)
            evento = self.env['account.event'].create(vals)
            record.account_event_id = evento
