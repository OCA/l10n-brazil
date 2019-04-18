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

    move_ids = fields.One2many(
        string=u'Lançamentos contábeis',
        comodel_name='account.move',
        inverse_name='journal_id',
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

    active = fields.Boolean(
        string='Ativo',
        default=True,
    )

    @api.multi
    @api.onchange('divisao_resultado_ids')
    def _verifica_porcentagem_fechamento(self):
        for record in self:
            # Verifica se o somatório das sequencias ultrapassam 100%
            for r in set(
                    [ja.sequencia for ja in record.divisao_resultado_ids]):
                if sum(a.porcentagem for a in
                       record.divisao_resultado_ids.filtered(
                           lambda x: x.sequencia == r)) > 100:

                    raise Warning(u'Porcentagem ultrapassa 100%.')

    @api.multi
    def atualizar_historico_lancamentos(self):
        self.ensure_one()

        if self.template_historico_padrao_id:
            historico_padrao = \
                self.template_historico_padrao_id.get_historico_padrao()
            for line in self.move_ids.mapped('line_id'):
                line.atualizar_nome(historico_padrao=historico_padrao)

        else:
            raise Warning(u'Necessário definir um Template Padrão do '
                          u'Lançamento para atualização dos históricos '
                          u'padrões')
