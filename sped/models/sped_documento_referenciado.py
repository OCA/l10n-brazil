# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from odoo import fields, models
from ..constante_tributaria import *


class DocumentoReferenciado(models.Model):
    _description = 'Documento Referenciado no Documento Fiscal'
    _name = 'sped.documento.referenciado'

    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento',
        ondelete='cascade',
        required=True,
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string=u'Empresa',
        related='documento_id.empresa_id',
        readonly=True,
    )
    data_emissao = fields.Date(
        string=u'Data de emissão',
        related='documento_id.data_emissao',
        readonly=True,
    )
    documento_referenciado_id = fields.Many2one(
        comodel_name='sped.documento',
        string=u'Documento referenciado',
        ondelete='restrict',
        domain=[('modelo', 'in', MODELO_FISCAL_REFERENCIADO_FILTRO)],
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Participante',
        domain=[('cnpj_cpf', '!=', False)],
        ondelete='restrict',
    )
    modelo = fields.Selection(
        selection=MODELO_FISCAL_REFERENCIADO,
        string=u'Modelo',
    )
    serie = fields.Char(
        string=u'Série',
        size=3,
    )
    numero = fields.Float(
        string=u'Número',
        digits=(18, 0),
    )
    data_emissao = fields.Date(
        string=u'Data de emissão',
    )
    chave = fields.Char(
        string=u'Chave',
        size=44,
    )
    numero_ecf = fields.Char(
        string=u'Nº do ECF',
        size=3,
    )
    numero_coo = fields.Integer(
        string=u'Nº do COO',
    )
