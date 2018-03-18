# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


class L10n_brMdfeLacre(models.Model):

    _name = b'l10n_br.mdfe.lacre'
    _description = 'Lacre do MDF-E'

    name = fields.Char()
    documento_id = fields.Many2one(
        comodel_name='sped.documento'
    )
