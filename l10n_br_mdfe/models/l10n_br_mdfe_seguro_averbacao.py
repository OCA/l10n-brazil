# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    RESPONSAVEL_SEGURO,
)


class L10nBrMdfeSeguroAverbacao(models.Model):

    _name = b'l10n_br.mdfe.seguro.averbacao'
    _description = 'Mdfe Seguro Averbação'
    name = fields.Char(
        string='Numero da averbação',
        size=40,
    )
    seguro_id = fields.Many2one(
        comodel_name='l10n_br.mdfe.seguro',

    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        related='seguro_id.documento_id',
        store=True,
    )