# Copyright 2017 KMEE INFORMATICA LTDA
# Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, fields


class ConfiguracaoImpressora(models.Model):
    _name = 'l10n_br_fiscal.pos_printer_config'
    _description = 'Terminal POS'

    name = fields.Char(
        string='Nome')

    printer_model = fields.Selection(
        selection=[
            ('bematech', 'Bematech MP-4200 TH'),
            ('daruma', 'Daruma DR700'),
            ('elgini9', 'Elgin I9'),
            ('elgini7', 'Elgin I7'),
            ('epson', 'Epson TM-T20'),
        ],
        string='Modelo')

    printer_method = fields.Selection([
        ('usb', 'USB'),
        ('file', 'File'),
        ('rede', 'Rede'),
        ('serial', 'Serial'),
        ('dummy', 'Dummy')
    ], string='Forma de Impressão')

    printer_string = fields.Char(
        string='Conexão')

    pos_config_ids = fields.One2many(
        comodel_name='l10n_br_fiscal.pos_config',
        inverse_name='printer_config_id',
        string='Pontos de Venda'
    )
