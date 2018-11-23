# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMapeamentoDePara(models.Model):
    _name = 'account.mapeamento'
    _description = u'Mapeamento do plano de contas do sistemas para ' \
                   u'os "n" planos de contas necessários'
    _order = 'referencia_plano_id, conta_sistema_id'

    name = fields.Char(
        string='Nome',
        compute='_get_display_name',
    )

    referencia_plano_id = fields.Many2one(
        string='Referência Plano de Contas',
        comodel_name='account.mapeamento.referencia',
    )
    conta_sistema_id = fields.Many2one(
        string='Conta do Sistema',
        comodel_name='account.account',
    )
    conta_plano_conta_externo = fields.Char(
        string='Conta Externa',
        help='Conta de um Plano de Contas externo ao sistema',
    )
    mapeamento_pai_id = fields.Many2one(
        string='Mapeamento Pai',
        comodel_name='account.mapeamento',
    )

    @api.multi
    def _get_display_name(self):
        for record in self:
            record.name = '{} - {}'.format(
                record.referencia_plano_id.name,
                record.conta_plano_conta_externo
            )

    def montar_dominio_busca_mapeamento(self, ref_plano, conta_interna=False,
                                        conta_externa=False):
        """
        Função responsável por montar o domain da busca dos mapeamentos
        verificando quais parâmetros foram passados.
        """
        domain = [
            ('referencia_plano_id', '=', ref_plano.id),
        ]

        if conta_interna:
            domain.append(('conta_sistema_id', '=', conta_interna.id))

        if conta_externa:
            domain.append(('conta_plano_conta_externo', '=', conta_externa.id))

        return domain

    def buscar_mapeamento(self, ref_plano, conta_interna=False,
                          conta_externa=False):
        """
        Função responsável para retornar os recordsets dos mapeamentos baseados
        nos parâmetros passados para a busca.
        """
        domain = self.montar_dominio_busca_mapeamento(
            ref_plano, conta_interna, conta_externa
        )

        mapeamento_ids = self.search(domain)

        return mapeamento_ids


class AccountMapeamentoReferenciaPlano(models.Model):
    _name = 'account.mapeamento.referencia'
    _description = u'Referência dos Planos de Contas Externos'

    name = fields.Char(
        string='Nome do Plano de Contas',
    )
