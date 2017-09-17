# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class FinanDocumento(models.Model):
    _name = b'finan.documento'
    _description = 'Tipo de Documento'
    _rec_name = 'nome'
    _order = 'nome'

    nome = fields.Char(
        string='Tipo de documento',
        size=30,
        required=True,
        index=True,
    )
    antecipa_vencimento = fields.Boolean(
        string='Antecipa vencimento?',
    )
