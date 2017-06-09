# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResBankAgencia(models.Model):

    _name = 'res.bank.agencia'

    name = fields.Char(
        string=u'Agência'
    )
    banco_id = fields.Many2one(
        comodel_name='res.bank',
        string=u'Banco'
    )
    pais_id = fields.Many2one(
        comodel_name='res.country',
        string=u'País'
    )
    estado_id = fields.Many2one(
        comodel_name='res.country.state',
        string=u'Estado'
    )
    cidade_id = fields.Many2one(
        comodel_name='l10n_br_base.city',
        string=u'Municipio',
        domain="[('state_id','=',state_id)]"
    )
    bairro = fields.Char(
        string=u'Bairro',
        size=32
    )
    rua = fields.Char(
        string=u'Rua'
    )
    numero = fields.Char(
        string=u'Número',
        size=10
    )
