# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.constante_tributaria import (
    AMBIENTE_MDFE,
    TIPO_EMISSAO_MDFE,
)


class SpedEmpresa(models.Model):

    _inherit = b'sped.empresa'

    ambiente_mdfe = fields.Selection(
        selection=AMBIENTE_MDFE,
        string='Ambiente MDF-E'
    )
    tipo_emissao_mdfe = fields.Selection(
        selection=TIPO_EMISSAO_MDFE,
        string='Tipo de emissão MDF-E'
    )
    serie_mdfe_producao = fields.Char(
        selection='Série em produção',
        size=3,
        default='1'
    )
    serie_mdfe_homologacao = fields.Char(
        string='Série em homologação',
        size=3,
        default='100'
    )
    serie_mdfe_contingencia_producao = fields.Char(
        string='Série em homologação',
        size=3,
        default='900'
    )
    serie_mdfe_contingencia_homologacao = fields.Char(
        string='Série em produção',
        size=3,
        default='999'
    )
    tipo_emissao_mdfe_contingencia = fields.Selection(
        selection=TIPO_EMISSAO_MDFE,
        string='Tipo de emissão MDF-E contingência'
    )
