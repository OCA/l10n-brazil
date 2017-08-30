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


class SpedParticipante(models.Model):
    _name = b'sped.participante'
    _description = 'Participantes'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = 'mail.thread'
    _rec_name = 'nome'
    _order = 'nome, cnpj_cpf'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner original',
        ondelete='restrict',
        required=True,
    )
    codigo = fields.Char(
        string='Código',
        size=60,
        index=True
    )
    nome = fields.Char(
        string='Nome',
        size=60,
        index=True
    )
    eh_orgao_publico = fields.Boolean(
        string='É órgão público?',
    )
    eh_cooperativa = fields.Boolean(
        string='É cooperativa?',
    )
    eh_sindicato = fields.Boolean(
        string='É sindicato?',
    )
    eh_consumidor_final = fields.Boolean(
        string='É consumidor final?',
    )
    # eh_sociedade = fields.Boolean('É sociedade?')
    eh_convenio = fields.Boolean(
        string='É convênio?',
    )
    eh_cliente = fields.Boolean(
        string='É cliente?',
    )
    eh_fornecedor = fields.Boolean(
        string='É fornecedor?',
    )
    eh_transportadora = fields.Boolean(
        string='É transportadora?'
    )
    # empresa_ids = fields.One2many(
    # 'res.company', 'partner_id', 'Empresa/unidade')
    # usuario_ids = fields.One2many('res.users', 'partner_id', 'Usuário')
    eh_grupo = fields.Boolean(
        string='É grupo?',
        index=True,
    )
    eh_empresa = fields.Boolean(
        string='É empresa?',
        index=True,
    )
    eh_usuario = fields.Boolean(
        string='É usuário?',
        index=True
    )
    eh_funcionario = fields.Boolean(
        string='É funcionário?'
    )
    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        size=18,
        index=True,
        help=u"""Para participantes estrangeiros, usar EX9999,
        onde 9999 é um número a sua escolha"""
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
    #
    # Telefone e email para a emissão da NF-e
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
    #
    # Inscrições e registros
    #
    contribuinte = fields.Selection(
        selection=INDICADOR_IE_DESTINATARIO,
        string='Contribuinte',
        default=INDICADOR_IE_DESTINATARIO_ISENTO
    )
    ie = fields.Char(
        string='Inscrição estadual',
        size=18
    )
    im = fields.Char(
        string='Inscrição municipal',
        size=14
    )
    suframa = fields.Char(
        string='SUFRAMA',
        size=12
    )
    rntrc = fields.Char(
        string='RNTRC',
        size=15
    )
    cei = fields.Char(
        string='CEI',
        size=15
    )
    rg_numero = fields.Char(
        string='RG',
        size=14
    )
    rg_orgao_emissor = fields.Char(
        string='Órgão emisssor do RG',
        size=20
    )
    rg_data_expedicao = fields.Date(
        string='Data de expedição do RG'
    )
    crc = fields.Char(
        string='Conselho Regional de Contabilidade',
        size=14
    )
    crc_uf = fields.Many2one(
        comodel_name='sped.estado',
        string='UF do CRC',
        ondelete='restrict'
    )
    profissao = fields.Char(
        string='Cargo',
        size=40
    )
    # 'sexo = fields.selection(SEXO, 'Sexo' )
    # 'estado_civil = fields.selection(ESTADO_CIVIL, 'Estado civil')
    pais_nacionalidade_id = fields.Many2one(
        comodel_name='sped.pais',
        string='Nacionalidade',
        ondelete='restrict'
    )
    #
    # Campos para o RH
    #
    codigo_sindical = fields.Char(
        comodel_name='Código sindical',
        size=30
    )
    codigo_ans = fields.Char(
        comodel_name='Código ANS',
        size=6
    )
    #
    # Para a NFC-e, ECF, SAT
    #
    exige_cnpj_cpf = fields.Boolean(
        comodel_name='Exige CNPJ/CPF?',
        compute='_compute_exige_cadastro_completo',
    )
    exige_endereco = fields.Boolean(
        comodel_name='Exige endereço?',
        compute='_compute_exige_cadastro_completo',
    )
    #
    # Para a contabilidade
    #
    # sociedade_ids = fields.One2many(
    #   'res.partner.sociedade', 'partner_id', 'Sociedade')

    #
    # Endereços e contatos
    #
    # address_ids = fields.One2many(
    #   'res.partner.address', 'partner_id', 'Contatos e endereços')

    #
    # Para o faturamento
    #
    transportadora_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Transportadora',
        ondelete='restrict',
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
        index=True,
    )
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        ondelete='restrict',
        domain=[('forma_pagamento', '!=', False)],
    )

    @api.depends('cnpj_cpf')
    def _compute_tipo_pessoa(self):
        for participante in self:
            participante.tipo_pessoa = 'I'

            if participante.cnpj_cpf:
                if participante.cnpj_cpf[:2] == 'EX':
                    participante.tipo_pessoa = 'E'
                    participante.contribuinte = (
                        INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE
                    )

                elif len(participante.cnpj_cpf) == 18:
                    participante.tipo_pessoa = 'J'
                    participante.contribuinte = (
                        INDICADOR_IE_DESTINATARIO_ISENTO
                    )

                else:
                    participante.tipo_pessoa = 'F'
                    participante.contribuinte = (
                        INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE
                    )

    @api.depends('eh_consumidor_final', 'endereco', 'numero', 'complemento',
                 'bairro', 'municipio_id', 'cep', 'eh_cliente',
                 'eh_fornecedor')
    def _compute_exige_cadastro_completo(self):
        for participante in self:
            if not participante.eh_consumidor_final or \
                    participante.eh_fornecedor:
                self.exige_cnpj_cpf = True
                self.exige_endereco = True
                continue

            self.exige_cnpj_cpf = False

            if (self.endereco or self.numero or self.complemento or
                    self.bairro or self.cep):
                self.exige_endereco = True
            else:
                self.exige_endereco = False

    @api.multi
    def name_get(self):
        res = []

        for participante in self:
            nome = participante.nome

            if participante.razao_social:
                if participante.nome.strip().upper() != \
                        participante.razao_social.strip().upper():
                    nome += ' - '
                    nome += participante.razao_social

            if participante.cnpj_cpf:
                nome += ' ['
                nome += participante.cnpj_cpf
                nome += '] '

            res.append((participante.id, nome))

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name and operator in ('=', 'ilike', '=ilike', 'like'):
            if operator != '=':
                name = name.strip().replace(' ', '%')

            args += [
                '|',
                ('codigo', '=', name),
                '|',
                ('nome', 'ilike', name),
                '|',
                ('razao_social', 'ilike', name),
                '|',
                ('fantasia', 'ilike', name),
                '|',
                ('cnpj_cpf', 'ilike', mascara(name, '  .   .   /    -  ')),
                ('cnpj_cpf', 'ilike', mascara(name, '   .   .   -  ')),
            ]
            participantes = self.search(args, limit=limit)
            return participantes.name_get()

        return super(SpedParticipante, self).name_search(name=name, args=args,
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
            valores['regime_tributario'] = REGIME_TRIBUTARIO_SIMPLES
            valores['contribuinte'] = INDICADOR_IE_DESTINATARIO_ISENTO

        else:
            valores['cnpj_cpf'] = formata_cpf(cnpj_cpf)
            valores['tipo_pessoa'] = TIPO_PESSOA_FISICA
            valores['regime_tributario'] = REGIME_TRIBUTARIO_LUCRO_PRESUMIDO
            valores['contribuinte'] = \
                INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        if cnpj_cpf[:2] == 'EX':
            valores['tipo_pessoa'] = TIPO_PESSOA_ESTRANGEIRO
            valores['regime_tributario'] = REGIME_TRIBUTARIO_LUCRO_PRESUMIDO
            valores['contribuinte'] = \
                INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

        if self.id:
            cnpj_ids = self.search(
                [('cnpj_cpf', '=', cnpj_cpf), ('id', '!=', self.id),
                 ('eh_empresa', '=', False), ('eh_grupo', '=', False)])
        else:
            cnpj_ids = self.search(
                [('cnpj_cpf', '=', cnpj_cpf), ('eh_empresa', '=', False),
                 ('eh_grupo', '=', False)])

        if len(cnpj_ids) > 0:
            raise ValidationError(_(u'CNPJ/CPF já existe no cadastro!'))

        return res

    @api.constrains('cnpj_cpf')
    def constrains_cnpj_cpf(self):
        for participante in self:
            participante._valida_cnpj_cpf()

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
        for participante in self:
            participante._valida_fone()

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
        for participante in self:
            participante._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        return self._valida_cep()

    def _valida_ie(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.suframa:
            if not valida_inscricao_estadual(self.suframa, 'SUFRAMA'):
                raise ValidationError(_(u'Inscrição na SUFRAMA inválida!'))

            valores['suframa'] = formata_inscricao_estadual(self.suframa,
                                                            'SUFRAMA')

        if self.ie:
            if self.contribuinte == '2' or self.contribuinte == '3':
                valores['ie'] = ''

            else:
                if not self.municipio_id:
                    raise ValidationError(_(
                        u"""Para validação da inscrição estadual é preciso
                        informar o município!"""))

                if self.ie.strip().upper()[
                   :6] == 'ISENTO' or self.ie.strip().upper()[:6] == 'ISENTA':
                    raise ValidationError(_(
                        u'Inscrição estadual inválida para contribuinte!'))

                if not valida_inscricao_estadual(
                        self.ie, self.municipio_id.estado_id.uf):
                    raise ValidationError(_(u'Inscrição estadual inválida!'))

                valores['ie'] = formata_inscricao_estadual(
                    self.ie, self.municipio_id.estado_id.uf
                )

        return res

    @api.constrains('suframa', 'ie', 'municipio_id', 'contribuinte')
    def _constrains_ie(self):
        for participante in self:
            participante._valida_ie()

    @api.onchange('suframa', 'ie', 'municipio_id', 'contribuinte')
    def _onchange_ie(self):
        return self._valida_ie()

    def _valida_email(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.email:
            email = self.email
            emails_validos = []

            if ',' not in email:
                email = self.email + ','

            for e in email.split(','):
                if e.strip() == '':
                    continue

                try:
                    valido = validate_email(e.strip())
                    emails_validos.append(valido['email'])
                except:
                    raise ValidationError(_(u'Email %s inválido!' % e.strip()))

            valores['email'] = ','.join(emails_validos)

        if self.email_nfe:
            email = self.email_nfe
            emails_validos = []

            if ',' not in email:
                email = self.email + ','

            for e in email.split(','):
                if e.strip() == '':
                    continue

                try:
                    valido = validate_email(e.strip())
                    emails_validos.append(valido['email'])
                except:
                    raise ValidationError(
                        _(u'Email %s inválido!' % e.strip()))

            valores['email_nfe'] = ','.join(emails_validos)

        return res

    @api.constrains('email', 'email_nfe')
    def constrains_email(self):
        for participante in self:
            participante._valida_email()

    @api.onchange('email', 'email_nfe')
    def onchange_email(self):
        return self._valida_email()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        if (not view_id) and (view_type == 'form') and self._context.get(
                'force_email'):
            view_id = self.env.ref(
                'sped.cadastro_participante_cliente_form').id
        res = super(SpedParticipante, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        # if view_type == 'form':
        #    res['arch'] = self.fields_view_get_address(res['arch'])
        return res

    @api.onchange('municipio_id')
    def onchange_municipio_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.municipio_id and self.municipio_id.cep_unico:
            valores['cep'] = self.municipio_id.cep_unico

        return res

    @api.onchange('nome', 'razao_social', 'fantasia', 'endereco', 'bairro',
                  'cidade', 'profissao')
    def onchange_nome(self):
        res = {}
        valores = {}
        res['value'] = valores

        # if self.nome:
        #    valores['nome'] = primeira_maiuscula(self.nome)

        # if self.razao_social:
        #    valores['razao_social'] = primeira_maiuscula(self.razao_social)

        # if self.fantasia:
        #    valores['fantasia'] = primeira_maiuscula(self.fantasia)

        # if self.endereco:
        #    valores['endereco'] = primeira_maiuscula(self.endereco)

        # if self.bairro:
        #    valores['bairro'] = primeira_maiuscula(self.bairro)

        # if self.cidade:
        #    valores['cidade'] = primeira_maiuscula(self.cidade)

        # if self.profissao:
        #    valores['profissao'] = primeira_maiuscula(self.profissao)

        return res

    def prepare_sync_to_partner(self):
        self.ensure_one()

        endereco = ''
        if self.endereco:
            endereco = self.endereco + ', ' + self.numero
            if self.complemento:
                endereco += ' - ' + self.complemento

        if self.fone and '+' not in self.fone:
            fone = '+55 ' + self.fone
        else:
            fone = self.fone

        if self.celular and '+' not in self.celular:
            celular = '+55 ' + self.celular
        else:
            celular = self.celular

        if self.fone_comercial and '+' not in self.fone_comercial:
            fax = '+55 ' + self.fone_comercial
        else:
            fax = self.fone_comercial

        vat = ''
        state_id = False
        country_id = self.env.ref('base.br').id
        if self.municipio_id:
            if self.municipio_id.pais_id.iso_3166_alfa_2 == 'BR':
                vat = 'BR-' + self.cnpj_cpf
                state_id = self.municipio_id.estado_id.state_id.id

            else:
                vat = (
                    self.municipio_id.pais_id.iso_3166_alfa_2 +
                    '-' +
                    self.cnpj_cpf[2:]
                )
                state_id = False

        zipcode = ''
        if self.cep:
            zipcode = 'BR-' + self.cep

        dados = {
            'ref': self.codigo,
            'name': self.nome,
            'street': endereco,
            'street2': self.bairro,
            'city': self.cidade,
            'zip': zipcode,
            'country_id': country_id,
            'state_id': state_id,
            'phone': fone,
            'mobile': celular,
            'fax': fax,
            'customer': self.eh_cliente,
            'supplier': self.eh_fornecedor,
            'website': self.site,
            'email': self.email,
            'vat': vat,
            'sped_participante_id': self.id,
            'is_company': self.tipo_pessoa == TIPO_PESSOA_JURIDICA,
        }

        if not self.partner_id.lang and self.env['res.lang'].search(
                [('code', '=', 'pt_BR')]):
                dados['lang'] = 'pt_BR'

        if not self.partner_id.tz:
            dados['tz'] = 'America/Sao_Paulo'

        return dados

    @api.multi
    def sync_to_partner(self):
        for participante in self:
            dados = participante.prepare_sync_to_partner()
            participante.partner_id.write(dados)

    @api.model
    def create(self, dados):
        if 'razao_social' in dados and not dados['razao_social']:
            dados['razao_social'] = dados['nome']

        dados['name'] = dados['nome']

        if not self.partner_id.lang and self.env['res.lang'].search(
                [('code', '=', 'pt_BR')]):
                dados['lang'] = 'pt_BR'

        if 'tz' not in dados:
            dados['tz'] = 'America/Sao_Paulo'
        participante = super(SpedParticipante, self).create(dados)
        participante.sync_to_partner()

        return participante

    @api.multi
    def write(self, dados):
        if 'nome' in dados:
            dados['name'] = dados['nome']

        res = super(SpedParticipante, self).write(dados)
        self.sync_to_partner()

        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.partner_id.customer:
            valores['eh_cliente'] = True
        else:
            valores['eh_cliente'] = False

        if self.partner_id.supplier:
            valores['eh_fornecedor'] = True
        else:
            valores['eh_fornecedor'] = False

        if self.partner_id.employee:
            valores['eh_funcionario'] = True
        else:
            valores['eh_funcionario'] = False

        if self.partner_id.original_company_id:
            valores['eh_empresa'] = True
        else:
            valores['eh_empresa'] = False

        if self.partner_id.original_user_id:
            valores['eh_usuario'] = True
        else:
            valores['eh_usuario'] = False
