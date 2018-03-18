# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

class L10nBrMdfeCondutor(models.Model):

    _name = b'l10n_br.mdfe.condutor'
    _description = 'Condutor MDF-E'

    @api.multi
    def _compute_cpf(self):
        for record in self:
            if record.cpf:
                record.cpj_numero = punctuation_rm(record.cpf)

    documento_id = fields.Many2one(
        comodel_name='sped.documento'
    )
    condutor_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Condutor',
    )
    name = fields.Char(
        string='Nome',
        related='condutor_id.nome',
        index = True,
        store = True,
    )
    cpf = fields.Char(
        string='CPF',
        size=15,
        index=True,
        store=True,
        related='condutor_id.cnpj_cpf'
    )
    cpf_numero = fields.Char(
        string='CPF (somente números)',
        size=11,
        compute='_compute_cpf',
        store=True,
        index=True,
    )
