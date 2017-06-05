# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright (C) 2017 - Daniel Sadamo - KMEE INFORMATICA
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import UserError


class SpedAccountMoveTemplate(models.Model):
    _name = b'sped.account.move.template'
    _description = 'Modelo de partidas dobradas'
    _rec_name = 'nome'

    nome = fields.Char(
        string='Descrição',
        required=True,
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name='sped.account.move.template',
        string='Modelo superior',
    )
    child_ids = fields.One2many(
        comodel_name='sped.account.move.template',
        inverse_name='parent_id',
        string='Modelos subordinados'
    )
    operacao_ids = fields.Many2many(
        comodel_name='sped.operacao',
        relation='sped_account_move_template_operacao',
        column1='template_id',
        column2='operacao_id',
        string='Operações Fiscais',
    )
    item_ids = fields.One2many(
        comodel_name='sped.account.move.template.item',
        inverse_name='template_id',
        string='Itens',
    )

    # @api.constrains('operacao_ids')
    # def _constraints_operacao_ids(self):
    #     for operacao in self.operacao_ids:
    #         if len(operacao.account_move_template_ids) > 1:
    #             raise UserError(u'A operação fiscal %s já tem um modelo de partidas dobradas vinculado!' % operacao.nome)
