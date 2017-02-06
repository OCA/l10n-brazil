# -*- coding: utf-8 -*-
# Copyright (C) 2016 KMEE (http://www.kmee.com.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, exceptions, _
from datetime import datetime


class L10nBrHrMediaslines(models.Model):
    _name = 'l10n_br.hr.medias.lines'
    _description = 'Brazilian HR - Linhas das Medias dos Proventos'
    # _order = 'year desc'

    parent_id = fields.Many2one(
        comodel_name='l10n_br.hr.medias',
        string='Medias pai',
    )

    nome_rubrica = fields.Char(
        string=u'Nome da Rubrica',
    )
    mes_1 = fields.Char(
        string=u'1º Mes',
        default='0',
    )
    mes_2 = fields.Char(
        string=u'2º Mes',
        default='0',
    )
    mes_3 = fields.Char(
        string=u'3º Mes',
        default='0',
    )
    mes_4 = fields.Char(
        string=u'4º Mes',
        default='0',
    )
    mes_5 = fields.Char(
        string=u'5º Mes',
        default='0',
    )
    mes_6 = fields.Char(
        string=u'6º Mes',
        default='0',
    )
    mes_7 = fields.Char(
        string=u'7º Mes',
        default='0',
    )
    mes_8 = fields.Char(
        string=u'8º Mes',
        default='0',
    )
    mes_9 = fields.Char(
        string=u'9º Mes',
        default='0',
    )
    mes_10 = fields.Char(
        string=u'10º Mes',
        default='0',
    )
    mes_11 = fields.Char(
        string=u'11º Mes',
        default='0',
    )
    mes_12 = fields.Char(
        string=u'12º Mes',
        default='0',
    )
    soma = fields.Float(
        string=u'Total dos Meses',
        compute='calcular_soma'
    )
    meses = fields.Float(
        string=u'Meses do periodo',
    )
    media = fields.Float(
        string=u'Média',
        compute='calcular_media',
    )
    media_texto = fields.Char(
        string=u'Média'
    )

    def calcular_soma(self):
        for linha in self:
            linha.soma = \
                float(linha.mes_1) + float(linha.mes_2) + float(linha.mes_3) +\
                float(linha.mes_4) + float(linha.mes_5) + float(linha.mes_6) +\
                float(linha.mes_7) + float(linha.mes_8) + float(linha.mes_9) +\
                float(linha.mes_10) + float(linha.mes_11) + float(linha.mes_12)

    def calcular_media(self):
        for linha in self:
            if linha.meses == 0:
                linha.media = 123
            else:
                linha.media = linha.soma/linha.meses