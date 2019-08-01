# -*- coding: utf-8 -*-
# Copyright 2019 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning

NOME_LANCAMENTO = {
    True: u'Ressarcimento(Provisão) ',
    False: u'Ressarcimento ',
}


class ContractRessarcimento(models.Model):
    _inherit = b'contract.ressarcimento'

    account_event_provisao_id = fields.Many2one(
        string=u'Evento Contábil Provisão',
        comodel_name='account.event',
        ondelete='restrict',
    )

    account_event_definitivo_id = fields.Many2one(
        string=u'Evento Contábil Definitivo',
        comodel_name='account.event',
        ondelete='restrict',
    )

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
            comp, line_ids = ('Ressarcimento(provisão)',
                              'contract_ressarcimento_provisionado_line_ids') \
                if record.valor_provisionado and not record.date_ressarcimento \
                else ('Ressarcimento', 'contract_ressarcimento_line_ids')

            for line in eval('record.'+line_ids):
                contabilizacao_rubricas.append((0, 0, {
                    'code': line.hr_salary_rule_id.code,
                    'valor': line.total,
                    'name': '{} - {}'.format(comp, line.name)
                }))

        return contabilizacao_rubricas

    @api.multi
    def button_aprovar(self):
        """
        Gera evento contábil quando aprovado.

        :return:
        """
        for record in self:
            try:
                if not record.account_event_provisao_id:
                    rubricas_para_contabilizar = self.gerar_contabilizacao_rubricas()

                    account_event = {
                        'ref': NOME_LANCAMENTO.get(record.valor_provisionado),
                        'data': record.date_provisao,
                        'account_event_line_ids': rubricas_para_contabilizar,
                        'origem': '{},{}'.format(
                            'contract.ressarcimento', record.id),
                    }

                    record.account_event_provisao_id = \
                        self.env['account.event'].create(account_event)

                    # Altera o state do Ressarcimento depois de gerar o evento contábil
                    super(ContractRessarcimento, self).button_aprovar()
                else:
                    # Reverte o evento contábil gerado a partir da provisão
                    record.account_event_provisao_id.button_reverter_lancamentos()

                    rubricas_para_contabilizar = \
                        self.gerar_contabilizacao_rubricas()

                    account_event = {
                        'ref': NOME_LANCAMENTO.get(
                            False if record.date_ressarcimento else True),
                        'data': record.date_ressarcimento,
                        'account_event_line_ids': rubricas_para_contabilizar,
                        'origem': '{},{}'.format(
                            'contract.ressarcimento', record.id),
                    }

                    record.account_event_definitivo_id = \
                        self.env['account.event'].create(account_event)

                    # Altera o state do Ressarcimento depois de gerar o evento contábil
                    super(ContractRessarcimento, self).button_aprovar()

            except Exception as e:
                Warning('Erro: {}'.format(e))
