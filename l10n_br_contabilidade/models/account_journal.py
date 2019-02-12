# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    name = fields.Char(
        string=u'Nome do Lote',
    )

    template_historico_padrao_id = fields.Many2one(
        string=u'Template Padrão do Lançamento',
        comodel_name='account.historico.padrao',
    )

    divisao_resultado_ids = fields.One2many(
        string=u'Contas para fechamento',
        comodel_name='account.divisao.resultado',
        inverse_name='journal_id',
    )

    account_lucro_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Conta - Lucro',
    )

    account_prejuizo_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Conta - Prejuízo',
    )

    ref = fields.Char(
        string='Origem do Lançamento',
        help='Definir Módulo de origem do lançamento.',
    )

    @api.multi
    @api.onchange('divisao_resultado_ids')
    def _verifica_porcentagem_fechamento(self):
        for record in self:
            # Verifica se o somatório das sequencias ultrapassam 100%
            for r in set([ja.sequencia for ja in record.divisao_resultado_ids]):
                if sum(a.porcentagem for a in record.divisao_resultado_ids.filtered(lambda x: x.sequencia == r)) > 100:
                    raise Warning(u'Porcentagem ultrapassa 100%.')

    # @api.model
    # def write(self, vals):
    #     res = super(AccountJournal, self).write(vals)
    #
    #     self._verifica_porcentagem_fechamento()
    #
    #     return res
