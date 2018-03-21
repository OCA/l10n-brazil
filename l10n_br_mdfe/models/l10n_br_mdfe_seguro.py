# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    RESPONSAVEL_SEGURO,
)


class L10nBrMdfeSeguro(models.Model):

    _name = b'l10n_br.mdfe.seguro'
    _description = 'Mdfe Seguro'

    documento_id = fields.Many2one(
        comodel_name='sped.documento'
    )

    responsavel_seguro = fields.Selection(
        selection=RESPONSAVEL_SEGURO,
        string='Responsável pelo seguro',
    )
    responsavel_cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        index=True,
        store=True,
    )
    seguradora_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Seguradora',
    )
    name = fields.Char(
        string='Nome da seguradora',
        related='seguradora_id.name',
        store=True,
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        index=True,
        related='seguradora_id.cnpj_cpf',
        store=True,
    )
    numero_apolice = fields.Char(
        string='Numero da apólice',
        size=20,
    )
    averbacao_ids = fields.One2many(
        comodel_name='l10n_br.mdfe.seguro.averbacao',
        inverse_name='seguro_id'
    )
    # TODO: Validar o CNPJ/ CPF
    # TODO: Formatar o CNPJ / CPF
