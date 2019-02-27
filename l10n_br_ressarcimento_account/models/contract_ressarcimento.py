# -*- coding: utf-8 -*-
# Copyright 2018 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date
from openerp import api, fields, models

NOME_LANCAMENTO = {
    'provisionado': u'Ressarcimento(Provisão)',
    'aprovado': u'Ressarcimento',
}


class ContractRessarcimento(models.Model):
    _inherit = b'contract.ressarcimento'

    account_event_id = fields.Many2one(
        string='Evento Contábil',
        comodel_name='account.event',
        ondelete='restrict',
    )

    # account_event_template_provisao_id = fields.Many2one(
    #     comodel_name='account.event.template',
    #     string='Roteiro contábil'
    # )
    #
    # account_move_ids = fields.One2many(
    #     comodel_name='account.move',
    #     inverse_name='contract_ressarcimento_id',
    #     string=u'Lançamentos',
    # )
    #
    # account_move_provisao_ids = fields.One2many(
    #     comodel_name='account.move',
    #     inverse_name='contract_ressarcimento_provisionado_id',
    #     string=u'Lançamentos',
    # )

    @api.multi
    def gerar_contabilizacao_rubricas(self):
        """
        Gerar um dict contendo a contabilização de cada rubrica
        return { string 'CODE' : float valor}
        """

        """
                {
            'data':         '2019-01-01',
            'lines':        [{'code': 'LIQUIDO', 'valor': 123,
                                'historico_padrao': {'mes': '01'}},
                             {'code': 'INSS', 'valor': 621.03}
                                'historico_padrao': {'nome': 'Nome do lança'}},
                            ],
            'ref':          identificação do módulo de origem
            'model':        (opcional) model de origem
            'res_id':       (opcional) id do registro de origem
            'period_id'     (opcional) account.period
            'company_id':   (opcional) res.company
        }
        """
        contabilizacao_rubricas = []

        # Roda as Rubricas e Cria os lançamentos contábeis
        for record in self:
            # se state = provisionado, pega as linhas do valor provisionado
            line_ids = 'contract_ressarcimento_provisionado_line_ids' \
                if record.state == 'provisionado' \
                else 'contract_ressarcimento_line_ids'

            for line in eval('record.'+line_ids):
                contabilizacao_rubricas.append((0, 0, {
                    'code': line.descricao,
                    'valor': line.total,
                }))

        return contabilizacao_rubricas

    @api.multi
    def button_aprovar(self):
        """

        :return:
        """
        for record in self:
            print record.state
            super(ContractRessarcimento, self).button_aprovar()
            print record.state
            # Exclui os Lançamento Contábeis anteriors
            record.account_event_id.unlink()

            rubricas_para_contabilizar = self.gerar_contabilizacao_rubricas()

            account_event = {
                'ref': '{} - {} - {}'.format(
                    NOME_LANCAMENTO.get(record.state),
                    record.account_period_id.name,
                    record.contract_id.employee_id.name),
                # 'data': record.date_from,
                'account_event_line_ids': rubricas_para_contabilizar,
            }

            record.account_event_id = \
                self.env['account.event'].create(account_event)


