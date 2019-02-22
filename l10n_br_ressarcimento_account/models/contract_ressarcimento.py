# -*- coding: utf-8 -*-
# Copyright 2018 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from openerp import api, fields, models


class ContractRessarcimento(models.Model):
    _inherit = b'contract.ressarcimento'

    account_event_template_id = fields.Many2one(
        comodel_name='account.event.template',
        string='Roteiro contábil'
    )

    account_event_template_provisao_id = fields.Many2one(
        comodel_name='account.event.template',
        string='Roteiro contábil'
    )

    account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='contract_ressarcimento_id',
        string=u'Lançamentos',
    )

    account_move_provisao_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='contract_ressarcimento_provisionado_id',
        string=u'Lançamentos',
    )

    @api.multi
    def button_aprovar(self):
        """

        :return:
        """
        super(ContractRessarcimento, self).button_aprovar()

        # Monta dict para lançamentos contábeis de acordo com o
        # roteiro escolhido
        dados = {
            'data': str(date.today()),
            'lines': [{'code': 'TOTAL',
                       'valor': self.total_provisionado
                       if self.state == 'provisionado' else self.total,
                       'name': self.account_event_template_id.name, }],
            'ref': 'Ressarcimento de Contrato',
            'model': 'contract.ressarcimento',
            'res_id': self.id,
            'period_id': self.account_period_provisao_id.id
            if self.state == 'provisionado' else self.account_period_id.id
        }

        if self.state == 'provisionado':
            self.account_move_provisao_ids = \
                self.account_event_template_provisao_id.gerar_contabilizacao(
                    dados=dados)
        else:
            self.account_move_ids = self.account_event_template_id.\
                gerar_contabilizacao(dados=dados)
