# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ConfiguracaoPDV(models.Model):
    _name = 'pdv.config'
    name = fields.Char(
        String=u"Nome do PDV",
        required=True
    )

    vendedor = fields.Many2one(
        comodel_name='res.users',
        string=u'Vendedor',
    )

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

    path_integrador = fields.Char(
        string=u'Caminho do Integrador'
    )

    ip = fields.Char(string=u'IP')

    porta = fields.Char(
        string=u'Porta'
    )

    ambiente = fields.Selection([
        ('producao', 'Produção'),
        ('homologacao', 'Homologação'),
    ], string=u'Ambiente')

    codigo_ativacao = fields.Char(string=u'Código de Ativação')

    cnpjsh = fields.Char(string=u'CNPJ Homologação')

    ie = fields.Char(string=u'Inscrição Estadual Homologação')

    chave_ativacao = fields.Char(string=u'Chave de Ativação')

    cnpj_software_house = fields.Char(
        string=u"CNPJ Software House"
    )

    assinatura = fields.Char(
        string=u"Assinatura"
    )

    chave_acesso_validador = fields.Char(
        string=u"Codigo de Ativação",
    )
    chave_requisicao = fields.Char(string=u'Chave de Requisição')
    estabelecimento = fields.Char(string=u'Estabelecimento')
    serial_pos = fields.Char(string=u'Serial POS')
    id_fila_validador = fields.Char(string=u'ID Fila Validador')
    multiplos_pag = fields.Boolean(string=u'Habilitar Múltiplos Pagamentos')
    anti_fraude = fields.Boolean(string=u'Habilitar Anti-Fraude')
