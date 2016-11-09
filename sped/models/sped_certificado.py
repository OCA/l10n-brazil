# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
import pysped


class Certificado(models.Model):
    _description = 'Certificado Digital'
    _name = 'sped.certificado'
    _rec_name = 'tipo'
    _order = 'data_fim_validade desc'

    tipo = fields.Selection(TIPO_CERTIFICADO, default=TIPO_CERTIFICADO_A1)
    numero_serie = fields.Char('Nº de série', size=32)
    senha = fields.Char('Senha', max_length=120)
    proprietario = fields.Char('Proprietário', max_length=120)
    cnpj_cpf = fields.Char('CNPJ/CPF', size=18)
    data_inicio_validade = fields.Datetime('Válido de')
    data_fim_validade = fields.Datetime('Válido até')
    arquivo = fields.Binary('Arquivo', attachment=True)
    nome_arquivo = fields.Char('Arquivo', size=255)

    @api.onchange('arquivo', 'senha')
    def onchange_arquivo_senha(self):
        res = {}
        valores = {}
        res['value'] = valores

        if not (self.arquivo and self.senha):
            return res

        open('/tmp/cert.pfx', 'w').write(self.arquivo)
        cert = pysped.xml_sped.certificado.Certificado()
        cert.arquivo = '/tmp/cert.pfx'
        cert.senha = self.senha

        cert.prepara_certificado_arquivo_pfx()
        valores['data_inicio_validade'] = str(cert.data_inicio_validade)
        valores['data_fim_validade'] = str(cert.data_fim_validade)
        valores['proprietario'] = cert.proprietario_nome
        valores['cnpj_cpf'] = cert.proprietario_cnpj

        return res
