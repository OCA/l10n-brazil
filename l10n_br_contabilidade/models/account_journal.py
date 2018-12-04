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

    @api.multi
    @api.onchange('divisao_resultado_ids')
    def _verifica_porcentagem_fechamento(self):
        for record in self:
            # Verifica se o somatório das sequencias ultrapassam 100%
            for r in set([ja.sequencia for ja in record.divisao_resultado_ids]):
                if sum(a.porcentagem for a in record.divisao_resultado_ids.filtered(lambda x: x.sequencia == r)) > 100:
                    raise Warning(u'Porcentagem ultrapassa 100%.')

    @api.model
    def write(self, vals):
        res = super(AccountJournal, self).write(vals)

        self._verifica_porcentagem_fechamento()

        return res


class AccountRateioResultado(models.Model):
    _name = 'account.divisao.resultado'
    _description = 'Vincula Contas ao Fechamento para informar porcentagem'
    _order = 'account_id'
    _sql_constraints = [
        ('account_journal_ident_unique', 'unique(account_id, journal_id)',
         'Contas para Fechamento duplicadas.'),
    ]

    account_id = fields.Many2one(
        string=u'Conta',
        comodel_name='account.account',
    )

    journal_id = fields.Many2one(
        string=u'Diário',
        comodel_name='account.journal',
    )

    porcentagem = fields.Float(
        string=u'Porcentagem'
    )

    sequencia = fields.Integer(
        string=u'Sequência',
        default=1,
    )

