# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models
from odoo.addons.l10n_br_base.constante_tributaria import *


class SpedDocumentoReferenciado(models.Model):
    _name = b'sped.documento.referenciado'
    _description = 'Documentos Referenciados no Documento Fiscal'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento',
        ondelete='cascade',
        required=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        related='documento_id.empresa_id',
        readonly=True,
    )
    data_emissao = fields.Date(
        string='Data de emissão',
        related='documento_id.data_emissao',
        readonly=True,
    )
    documento_referenciado_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento referenciado',
        ondelete='restrict',
        domain=[('modelo', 'in', MODELO_FISCAL_REFERENCIADO_FILTRO)],
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
        domain=[('cnpj_cpf', '!=', False)],
        ondelete='restrict',
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL_REFERENCIADO,
        string='Modelo',
    )
    serie = fields.Char(
        string='Série',
        size=3,
    )
    numero = fields.Float(
        string='Número',
        digits=(18, 0),
    )
    data_emissao = fields.Date(
        string='Data de emissão',
    )
    chave = fields.Char(
        string='Chave',
        size=44,
    )
    numero_ecf = fields.Char(
        string='Nº do ECF',
        size=3,
    )
    numero_coo = fields.Integer(
        string='Nº do COO',
    )
