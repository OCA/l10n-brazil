# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from odoo import models, fields


class ConfiguracaoImpressora(models.Model):
    _name = 'impressora.config'
    _rec_name = 'nome'

    impressora = fields.One2many(
        'pdv.config',
        'impressora',
        domain='Nome'
    )

    modelo = fields.Selection([
        ('bematech', 'Bematech MP-4200 TH'),
        ('daruma', 'Daruma DR700'),
        ('elgini9', 'Elgin I9'),
        ('elgini7', 'Elgin I7'),
        ('epson', 'Epson TM-T20'),

    ], string=u'Modelo')
    forma = fields.Selection([
        ('usb', 'USB'),
        ('file', 'File'),
        ('rede', 'Rede'),
        ('serial', 'Serial'),
        ('dummy', 'Dummy')
    ], string=u'Forma de Impressão')
    conexao = fields.Char(string=u'Conexão')

    nome = fields.Char(string=u'Nome')
