# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from ..constante_tributaria import *
import pysped
from pybrasil.inscricao import formata_cnpj, formata_cpf, valida_cnpj, valida_cpf
from pybrasil.data import formata_data
from datetime import datetime


class Certificado(models.Model):
    _description = 'Certificado Digital'
    _name = 'sped.certificado'
    _rec_name = 'descricao'
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

    @api.one
    @api.constrains('tipo', 'senha', 'arquivo')
    def constrains_certificado(self):
        if self.tipo != TIPO_CERTIFICADO_A1:
            return

        open('/tmp/cert.pfx', 'w').write(self.arquivo.decode('base64'))
        cert = pysped.xml_sped.certificado.Certificado()
        cert.arquivo = '/tmp/cert.pfx'
        cert.senha = self.senha

        cert.prepara_certificado_arquivo_pfx()

        self.numero_serie = str(cert.numero_serie)
        self.data_inicio_validade = str(cert.data_inicio_validade)
        self.data_fim_validade = str(cert.data_fim_validade)
        self.proprietario = cert.proprietario_nome

        if valida_cpf(cert.proprietario_cnpj):
            self.cnpj_cpf = formata_cpf(cert.proprietario_cnpj)
        elif valida_cnpj(cert.proprietario_cnpj):
            self.cnpj_cpf = formata_cnpj(cert.proprietario_cnpj)
        else:
            self.cnpj_cpf = cert.proprietario_cnpj

    @api.one
    @api.depends('tipo', 'numero_serie', 'proprietario', 'cnpj_cpf', 'data_inicio_validade', 'data_fim_validade')
    def _descricao(self):
        if self.tipo == TIPO_CERTIFICADO_A1:
            self.descricao = 'A1'
        else:
            self.descricao = 'A3'

        if self.proprietario:
            self.descricao += ' - ' + self.proprietario

        if self.cnpj_cpf:
            self.descricao += ' - ' + self.cnpj_cpf

        if self.data_inicio_validade and self.data_fim_validade:
            self.descricao += ', válido de '
            self.descricao += formata_data(self.data_inicio_validade)
            self.descricao += ' até '
            self.descricao += formata_data(self.data_fim_validade)

    descricao = fields.Char(string='Certificado digital', compute=_descricao, store=False)

    @api.one
    @api.depends('data_fim_validade')
    def _fora_validade(self):
        print(self.data_fim_validade, datetime.now(), str(datetime.now()), self.data_fim_validade <= str(datetime.now()))
        self.fora_validade = self.data_fim_validade <= str(datetime.now())

    fora_validade = fields.Char(string='Fora da validade?', size=1, compute=_fora_validade, store=False)
