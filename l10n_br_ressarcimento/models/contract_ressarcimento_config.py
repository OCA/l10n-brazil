# -*- coding: utf-8 -*-
# Copyright 2019 ABGF.gov.br Luciano Veras
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from time import gmtime, strftime
from openerp import api, fields, models, _


class ContractRessarcimentoConfig(models.Model):
    _name = b'contract.ressarcimento.config'
    _description = 'Configurações do Ressarcimento de Contrato'

    contract_ressarcimento_config_line_ids = fields.One2many(
        inverse_name='contract_ressarcimento_config_id',
        comodel_name='contract.ressarcimento.config.line',
        string='Ressarcimento do Contrato',
    )

    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Parceiros para notificar',
    )

    @api.multi
    def salvar_config(self):
        pass

    @api.multi
    def check_isset_ressarcimento(self, cr, uid, context=None):
        hoje = int(strftime("%d", gmtime()))
        competencia = strftime("%m/%Y", gmtime())

        for record in self:
            list_dias = record.contract_ressarcimento_config_line_ids.\
                    mapped('dia_limite')
            list_dias_prov = record.contract_ressarcimento_config_line_ids.\
                    mapped('dia_limite_provisao')

            if hoje in list_dias:
                print hoje
            if hoje in list_dias_prov:
                print hoje

            print competencia


class ContractRessarcimentoConfigLine(models.Model):
    _name = b'contract.ressarcimento.config.line'

    contract_ressarcimento_config_id = fields.Many2one(
        comodel_name='contract.ressarcimento.config',
        string='Configuração Ressarcimento',
    )

    contract_id = fields.Many2one(
        comodel_name="hr.contract",
        string="Contrato",
    )

    dia_limite = fields.Integer(
        string='Dia limite',
        default=10,
    )

    dia_limite_provisao = fields.Integer(
        string='Dia limite (provisão)',
        default=10,
    )
