# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConfiguracaoPDV(models.Model):
    _name = 'pdv.config'


    pdv_name = fields.Char(string=u'Nome')
    localizacao = fields.Char(string=u'Localização')

    numero_caixa = fields.Char(string=u'Número de caixa')
    tipo = fields.Selection([('SAT', 'SAT'),
                             ], string=u'Tipo')

    impressora = fields.Many2one(
        'impressora.config',
        'Impressora',
    )



    tipo_sat = fields.Selection([
        ('local', 'Local'),
        ('rede_interna', 'Rede Interna'),
        ('remoto', 'Remoto'),
    ], string=u'Tipo SAT')
    ip = fields.Char(string=u'IP')
    ambiente = fields.Selection([
        ('producao', 'Produção'),
        ('homologacao', 'Homologação'),
    ], string=u'Ambiente')
    codigo_ativacao = fields.Char(string=u'Código de Ativação')
    cnpjsh = fields.Char(string=u'CNPJ Homologação')
    ie = fields.Char(string=u'Inscrição Estadual Homologação')
    chave_ativacao = fields.Char(string=u'Chave de Ativação')