# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountCentroCusto(models.Model):
    _name = 'account.centro.custo'
    _description = 'Centro de Custo para lançamentos Contábeis'
    _order = 'name'

    name = fields.Char(
        string='Name',
        compute='compute_name',
        store=True,
    )

    nome = fields.Char(
        string='Nome',
    )

    descricao = fields.Char(
        string='Descrição',
    )

    @api.depends('nome','descricao')
    def compute_name(self):
        for centro in self:
            centro.name = centro.nome + ' - ' + centro.descricao
