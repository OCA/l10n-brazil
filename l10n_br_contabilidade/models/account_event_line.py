# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountEventLine(models.Model):
    _name = 'account.event.line'
    _order = 'name, code'

    account_event_id = fields.Many2one(
        string='Evento Contábil',
        comodel_name='account.event',
    )

    code = fields.Char(
        string='Code',
    )

    name = fields.Char(
        string='Name',
    )

    description = fields.Char(
        string='Description',
    )

    valor = fields.Float(
        string='Valor',
    )

    conta_debito_exclusivo_id = fields.Many2one(
        string=u'Conta de débito exclusiva',
        comodel_name='account.account',
    )

    conta_credito_exclusivo_id = fields.Many2one(
        string=u'Conta de crédito exclusiva',
        comodel_name='account.account',
    )

    account_move_id = fields.Many2one(
        string=u'Lançamento Relacionado',
        comodel_name='account.move',
    )
