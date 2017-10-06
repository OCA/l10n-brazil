# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .sped_base import SpedBase
from ..constante_tributaria import (
    INDICADOR_IE_DESTINATARIO,
    INDICADOR_IE_DESTINATARIO_ISENTO,
    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_SIMPLES,
    TIPO_PESSOA_JURIDICA,
    TIPO_PESSOA_FISICA,
    TIPO_PESSOA_ESTRANGEIRO,
)

_logger = logging.getLogger(__name__)

try:
    from email_validator import validate_email

    from pybrasil.base import mascara
    from pybrasil.inscricao import (formata_cnpj, formata_cpf,
                                    limpa_formatacao,
                                    formata_inscricao_estadual, valida_cnpj,
                                    valida_cpf, valida_inscricao_estadual)
    from pybrasil.telefone import (formata_fone, valida_fone_fixo,
                                   valida_fone_celular,
                                   valida_fone_internacional)

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedEndereco(models.Model):
    _name = b'sped.endereco'
    _description = 'Endereços de participantes'
    _inherit = 'mail.thread'
    _rec_name = 'endereco_completo'
    _order = 'endereco_completo'

    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante',
        ondelete='restrict',
    )
    nome = fields.Char(
        string='Nome',
        size=60,
        index=True
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        index=True,
        help=u"""Para participantes estrangeiros, usar EX9999,
        onde 9999 é um número a sua escolha"""
    )
    cnpj_cpf_raiz = fields.Char(
        string='Raiz do CNPJ/CPF',
        size=14,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True,
    )
    tipo_pessoa = fields.Char(
        string='Tipo pessoa',
        size=1,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True
    )
    razao_social = fields.Char(
        string='Razão Social',
        size=60,
        index=True
    )
    fantasia = fields.Char(
        string='Fantasia',
        size=60,
        index=True
    )
    endereco = fields.Char(
        string='Endereço',
        size=60
    )
    numero = fields.Char(
        string='Número',
        size=60
    )
    complemento = fields.Char(
        string='Complemento',
        size=60
    )
    bairro = fields.Char(
        string='Bairro',
        size=60
    )
    municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string='Município',
        ondelete='restrict'
    )
    cidade = fields.Char(
        string='Município',
        related='municipio_id.nome',
        store=True,
        index=True
    )
    estado = fields.Char(
        string='Estado',
        related='municipio_id.estado',
        store=True,
        index=True
    )
    cep = fields.Char(
        string='CEP',
        size=9
    )
    endereco_completo = fields.Char(
        string='Endereço',
        compute='_compute_endereco_completo',
        store=True,
        index=True,
    )
    #
    # Telefone e email
    #
    fone = fields.Char(
        string='Fone',
        size=18
    )
    fone_comercial = fields.Char(
        string='Fone Comercial',
        size=18
    )
    celular = fields.Char(
        string='Celular',
        size=18
    )
    email = fields.Char(
        string='Email',
        size=60
    )
    site = fields.Char(
        string='Site',
        size=60
    )
    email_nfe = fields.Char(
        string='Email para envio da NF-e',
        size=60
    )
    color = fields.Integer(
        string='Cor no kanban',
        default=0,
    )

    @api.depends('cnpj_cpf')
    def _compute_tipo_pessoa(self):
        for endereco in self:
            if not endereco.cnpj_cpf:
                endereco.tipo_pessoa = 'I'
                endereco.cnpj_cpf_raiz = ''
                continue

            if endereco.cnpj_cpf[:2] == 'EX':
                endereco.tipo_pessoa = 'E'
                endereco.cnpj_cpf_raiz = endereco.cnpj_cpf

            elif len(endereco.cnpj_cpf) == 18:
                endereco.tipo_pessoa = 'J'
                endereco.cnpj_cpf_raiz = endereco.cnpj_cpf[:10]

            else:
                endereco.tipo_pessoa = 'F'
                endereco.cnpj_cpf_raiz = endereco.cnpj_cpf

    @api.depends('endereco', 'numero', 'complemento', 'bairro',
                 'municipio_id', 'cep')
    def _compute_endereco_completo(self):
        for endereco in self:
            if not endereco.endereco:
                endereco.endereco_completo = ''
                continue

            endereco_completo = endereco.endereco
            endereco_completo += ', '
            endereco_completo += endereco.numero

            if endereco.complemento:
                endereco_completo += ' - '
                endereco_completo += endereco.complemento

            endereco_completo += ' - '
            endereco_completo += endereco.bairro
            endereco_completo += ' - '
            endereco_completo += endereco.cidade
            endereco_completo += '-'
            endereco_completo += endereco.estado
            endereco_completo += ' - '
            endereco_completo += endereco.cep
            endereco.endereco_completo = endereco_completo

    @api.multi
    def name_get(self):
        res = []

        for endereco in self:
            endereco_completo = endereco.endereco
            endereco_completo += ', '
            endereco_completo += endereco.numero

            if endereco.complemento:
                endereco_completo += ' - '
                endereco_completo += endereco.complemento

            endereco_completo += ' - '
            endereco_completo += endereco.bairro
            endereco_completo += ' - '
            endereco_completo += endereco.cidade
            endereco_completo += '-'
            endereco_completo += endereco.estado
            endereco_completo += ' - '
            endereco_completo += endereco.cep

            nome = ''
            if endereco.nome:
                nome = endereco.nome

            if endereco.cnpj_cpf:
                nome += ' ['
                nome += endereco.cnpj_cpf
                nome += '] '

            res.append((endereco.id, nome + endereco_completo))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += [
                '|',
                ('endereco', 'ilike', name),
                '|',
                ('bairro', 'ilike', name),
                '|',
                ('cidade', 'ilike', name),
                '|',
                ('nome', 'ilike', name),
                '|',
                ('razao_social', 'ilike', name),
                '|',
                ('cnpj_cpf', 'ilike', mascara(name, '  .   .   /    -  ')),
                ('cnpj_cpf', 'ilike', mascara(name, '   .   .   -  ')),
            ]
            enderecos = self.search(args, limit=limit)
            return enderecos.name_get()

        return super(SpedEndereco, self).name_search(name=name, args=args,
                                                     operator=operator,
                                                     limit=limit)

    def _valida_cnpj_cpf(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if not self.cnpj_cpf:
            return res

        cnpj_cpf = limpa_formatacao(self.cnpj_cpf or '')

        if cnpj_cpf[:2] != 'EX':
            if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                raise ValidationError(_(u'CNPJ/CPF inválido'))

        if len(cnpj_cpf) == 14:
            valores['cnpj_cpf'] = formata_cnpj(cnpj_cpf)
            valores['tipo_pessoa'] = TIPO_PESSOA_JURIDICA

        else:
            valores['cnpj_cpf'] = formata_cpf(cnpj_cpf)
            valores['tipo_pessoa'] = TIPO_PESSOA_FISICA

        if cnpj_cpf[:2] == 'EX':
            valores['tipo_pessoa'] = TIPO_PESSOA_ESTRANGEIRO

        return res

    @api.constrains('cnpj_cpf')
    def constrains_cnpj_cpf(self):
        for endereco in self:
            endereco._valida_cnpj_cpf()

    @api.onchange('cnpj_cpf')
    def onchange_cnpj_cpf(self):
        return self._valida_cnpj_cpf()

    def _valida_fone(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.fone:
            if (not valida_fone_internacional(self.fone)) and (
                    not valida_fone_fixo(self.fone)):
                raise ValidationError(_(u'Telefone fixo inválido!'))

            valores['fone'] = formata_fone(self.fone)

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (
                    not valida_fone_fixo(self.fone_comercial)) and (
                    not valida_fone_celular(self.fone_comercial)):
                raise ValidationError(_(u'Telefone comercial inválido!'))

            valores['fone_comercial'] = formata_fone(self.fone_comercial)

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (
                    not valida_fone_celular(self.celular)):
                raise ValidationError(_(u'Celular inválido!'))

            valores['celular'] = formata_fone(self.celular)

        return res

    @api.constrains('fone', 'celular', 'fone_comercial')
    def constrains_fone(self):
        for endereco in self:
            endereco._valida_fone()

    @api.onchange('fone', 'celular', 'fone_comercial')
    def onchange_fone(self):
        return self._valida_fone()

    def _valida_cep(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if not self.cep:
            return res

        cep = limpa_formatacao(self.cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise ValidationError(_(u'CEP inválido!'))

        valores['cep'] = cep[:5] + '-' + cep[5:]

        return res

    @api.constrains('cep')
    def constrains_cep(self):
        for endereco in self:
            endereco._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        return self._valida_cep()
