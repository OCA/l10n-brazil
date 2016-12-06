# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia - Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


from __future__ import division, print_function, unicode_literals

import logging
_logger = logging.getLogger(__name__)

try:
    import pysped

    from pybrasil.data import formata_data
    from pybrasil.inscricao import (formata_cnpj, formata_cpf, valida_cnpj,
                                    valida_cpf)

except (ImportError, IOError) as err:
    _logger.debug(err)

from datetime import datetime

from odoo import api, fields, models
from ..constante_tributaria import *


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
    descricao = fields.Char(string='Certificado digital', compute='_compute_descricao', store=False)
    fora_validade = fields.Char(string='Fora da validade?', size=1, compute='_compute_fora_validade', store=False)

    @api.depends('tipo', 'numero_serie', 'proprietario', 'cnpj_cpf', 'data_inicio_validade', 'data_fim_validade')
    def _compute_descricao(self):
        for certificado in self:
            if certificado.tipo == TIPO_CERTIFICADO_A1:
                certificado.descricao = 'A1'
            else:
                certificado.descricao = 'A3'

            if certificado.proprietario:
                certificado.descricao += ' - ' + certificado.proprietario

            if certificado.cnpj_cpf:
                certificado.descricao += ' - ' + certificado.cnpj_cpf

            if certificado.data_inicio_validade and certificado.data_fim_validade:
                certificado.descricao += ', válido de '
                certificado.descricao += formata_data(certificado.data_inicio_validade)
                certificado.descricao += ' até '
                certificado.descricao += formata_data(certificado.data_fim_validade)

    @api.depends('data_fim_validade')
    def _compute_fora_validade(self):
        for certificado in self:
            certificado.fora_validade = certificado.data_fim_validade <= str(datetime.now())

    @api.constrains('tipo', 'senha', 'arquivo')
    def _check_certificado(self):
        for certificado in self:
            if certificado.tipo != TIPO_CERTIFICADO_A1:
                continue

            open('/tmp/cert.pfx', 'w').write(certificado.arquivo.decode('base64'))
            cert = pysped.xml_sped.certificado.Certificado()
            cert.arquivo = '/tmp/cert.pfx'
            cert.senha = certificado.senha

            cert.prepara_certificado_arquivo_pfx()

            certificado.numero_serie = str(cert.numero_serie)
            certificado.data_inicio_validade = str(cert.data_inicio_validade)
            certificado.data_fim_validade = str(cert.data_fim_validade)
            certificado.proprietario = cert.proprietario_nome

            if valida_cpf(cert.proprietario_cnpj):
                certificado.cnpj_cpf = formata_cpf(cert.proprietario_cnpj)
            elif valida_cnpj(cert.proprietario_cnpj):
                certificado.cnpj_cpf = formata_cnpj(cert.proprietario_cnpj)
            else:
                certificado.cnpj_cpf = cert.proprietario_cnpj
