# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class FinanceiroTipo_documento(models.Model):

    _name = b'financeiro.tipo.documento'
    _description = 'Financeiro Tipo_documento'  # TODO

    name = fields.Char()
