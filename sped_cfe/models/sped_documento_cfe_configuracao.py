# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
# Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models

PRINTER = [
    ('epson-tm-t20', u'Epson TM-T20'),
    ('bematech-mp4200th', u'Bematech MP4200TH'),
    ('daruma-dr700', u'Daruma DR700'),
    ('elgin-i9', u'Elgin I9'),
]


class SpedDocumentoCfeConfiguracao(models.Model):
    _name = b'sped.documento.cfe.configuracao'

    company_id = fields.Many2one(
        string="Empresa",
        comodel_name="sped.empresa"
    )

    endereco_ip = fields.Char(
        string="Endereço Ip",
        required=True
    )

    cnpj_homologacao = fields.Char(
        string=u'CNPJ homologação',
        size=18
    )

    ie_homologacao = fields.Char(
        string=u'IE homologação',
        size=16
    )

    cnpj_software_house = fields.Char(
        string=u'CNPJ software house',
        size=18
    )

    sat_ambiente = fields.Selection(
        string=u'Ambiente SAT',
        selection=[
            ('hologacao', 'Hologação'),
            ('producao', 'Produção')
        ],
        store=True
    )

    sat_path = fields.Char(
        string=u'SAT path'
    )

    numero_caixa = fields.Integer(
        string=u'Número do Caixa',
        copy=False
    )

    cod_ativacao = fields.Char(
        string=u'Código de ativação',
    )

    impressora = fields.Selection(
        selection=PRINTER,
        string=u'Impressora',
    )

    printer_params = fields.Char(
        string=u'Printer parameters'
    )

    fiscal_category_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.category',
        string=u'Fiscal Category'
    )

    assinatura_sat = fields.Char(
        'Assinatura no CFe'
    )
