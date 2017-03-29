# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#


import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..constante_tributaria import (
    INDICADOR_IE_DESTINATARIO,
    INDICADOR_IE_DESTINATARIO_ISENTO,
    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_LUCRO_REAL,
    REGIME_TRIBUTARIO_SIMPLES,
    REGIME_TRIBUTARIO_SIMPLES_EXCESSO,
    TIPO_PESSOA_JURIDICA,
)

_logger = logging.getLogger(__name__)

try:
    from email_validator import validate_email

    from pybrasil.base import mascara, primeira_maiuscula
    from pybrasil.inscricao import (formata_cnpj, formata_cpf,
                                    limpa_formatacao,
                                    formata_inscricao_estadual, valida_cnpj,
                                    valida_cpf, valida_inscricao_estadual)
    from pybrasil.telefone import (formata_fone, valida_fone_fixo,
                                   valida_fone_celular,
                                   valida_fone_internacional)

except (ImportError, IOError) as err:
    _logger.debug(err)


class Participante(models.Model):
    _description = u'Participantes'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = 'mail.thread'
    _name = 'sped.participante'
    _rec_name = 'nome'
    _order = 'nome, cnpj_cpf'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=u'Partner original',
        ondelete='restrict',
        required=True,
    )
    codigo = fields.Char(
        string=u'Código',
        size=60,
        index=True
    )
    nome = fields.Char(
        string=u'uNome',
        size=60,
        index=True
    )
    eh_orgao_publico = fields.Boolean(
        string=u'É órgão público?',
    )
    eh_cooperativa = fields.Boolean(
        string=u'É cooperativa?',
    )
    eh_sindicato = fields.Boolean(
        string=u'É sindicato?',
    )
    eh_consumidor_final = fields.Boolean(
        string=u'É consumidor final?',
    )
    # eh_sociedade = fields.Boolean('É sociedade?')
    eh_convenio = fields.Boolean(
        string=u'É convênio?',
    )
    eh_cliente = fields.Boolean(
        string=u'É cliente?',
    )
    eh_fornecedor = fields.Boolean(
        string=u'É fornecedor?',
    )
    eh_transportadora = fields.Boolean(
        string=u'É transportadora?'
    )
    # empresa_ids = fields.One2many(
    # 'res.company', 'partner_id', 'Empresa/unidade')
    # usuario_ids = fields.One2many('res.users', 'partner_id', 'Usuário')
    eh_grupo = fields.Boolean(
        string=u'É grupo?',
        index=True,
    )
    eh_empresa = fields.Boolean(
        string=u'É empresa?',
        index=True,
    )
    eh_usuario = fields.Boolean(
        string=u'É usuário?',
        index=True
    )
    eh_funcionario = fields.Boolean(
        string=u'É funcionário?'
    )
    cnpj_cpf = fields.Char(
        string=u'CNPJ/CPF',
        size=18,
        index=True,
        help=u"""Para participantes estrangeiros, usar EX9999,
        onde 9999 é um número a sua escolha"""
    )
    tipo_pessoa = fields.Char(
        string=u'Tipo pessoa',
        size=1,
        compute='_compute_tipo_pessoa',
        store=True,
        index=True
    )
    razao_social = fields.Char(
        string=u'Razão Social',
        size=60,
        index=True
    )
    fantasia = fields.Char(
        string=u'Fantasia',
        size=60,
        index=True
    )
    endereco = fields.Char(
        string=u'Endereço',
        size=60
    )
    numero = fields.Char(
        string=u'Número',
        size=60
    )
    complemento = fields.Char(
        string=u'Complemento',
        size=60
    )
    bairro = fields.Char(
        string=u'Bairro',
        size=60
    )
    municipio_id = fields.Many2one(
        comodel_name='sped.municipio',
        string=u'Município',
        ondelete='restrict'
    )
    cidade = fields.Char(
        string=u'Município',
        related='municipio_id.nome',
        store=True,
        index=True
    )
    estado = fields.Char(
        string=u'Estado',
        related='municipio_id.estado',
        store=True,
        index=True
    )
    cep = fields.Char(
        string=u'CEP',
        size=9
    )
    #
    # Telefone e email para a emissão da NF-e
    #
    fone = fields.Char(
        string=u'Fone',
        size=18
    )
    fone_comercial = fields.Char(
        string=u'Fone Comercial',
        size=18
    )
    celular = fields.Char(
        string=u'Celular',
        size=18
    )
    email = fields.Char(
        string=u'Email',
        size=60
    )
    site = fields.Char(
        string=u'Site',
        size=60
    )
    email_nfe = fields.Char(
        string=u'Email para envio da NF-e',
        size=60
    )
    #
    # Inscrições e registros
    #
    contribuinte = fields.Selection(
        selection=INDICADOR_IE_DESTINATARIO,
        string=u'Contribuinte',
        default=INDICADOR_IE_DESTINATARIO_ISENTO
    )
    ie = fields.Char(
        string=u'Inscrição estadual',
        size=18
    )
    im = fields.Char(
        string=u'Inscrição municipal',
        size=14
    )
    suframa = fields.Char(
        string=u'SUFRAMA',
        size=12
    )
    rntrc = fields.Char(
        string=u'RNTRC',
        size=15
    )
    cnae_id = fields.Many2one(
        comodel_name='sped.cnae',
        string=u'CNAE principal'
    )
    cei = fields.Char(
        string=u'CEI',
        size=15
    )
    rg_numero = fields.Char(
        string=u'RG',
        size=14
    )
    rg_orgao_emissor = fields.Char(
        string=u'Órgão emisssor do RG',
        size=20
    )
    rg_data_expedicao = fields.Date(
        string=u'Data de expedição do RG'
    )
    crc = fields.Char(
        string=u'Conselho Regional de Contabilidade',
        size=14
    )
    crc_uf = fields.Many2one(
        comodel_name='sped.estado',
        string=u'UF do CRC',
        ondelete='restrict'
    )
    profissao = fields.Char(
        string=u'Cargo',
        size=40
    )
    # 'sexo = fields.selection(SEXO, 'Sexo' )
    # 'estado_civil = fields.selection(ESTADO_CIVIL, 'Estado civil')
    pais_nacionalidade_id = fields.Many2one(
        comodel_name='sped.pais',
        string=u'Nacionalidade',
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
        comodel_name=u'Exige CNPJ/CPF?',
        compute='_compute_exige_cadastro_completo',
    )
    exige_endereco = fields.Boolean(
        comodel_name=u'Exige endereço?',
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
        string=u'Transportadora',
        ondelete='restrict',
    )
    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string=u'Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
        index=True,
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

                # @api.depends('nome', 'razao_social', 'fantasia', 'cnpj_cpf')
                # def name_get(self, cr, uid, ids, context={}):
                # if not len(ids):
                # return []

                # res = []
                # for partner_obj in self.browse(cr, uid, ids):
                # if hasattr(partner_obj, 'nome'):
                # nome = partner_obj.nome or ''

                # if partner_obj.cnpj_cpf:
                # nome += ' - ' + partner_obj.cnpj_cpf

                # if partner_obj.razao_social and
                # partner_obj.razao_social.upper() != partner_obj.nome.upper():
                # nome += ' [' + partner_obj.razao_social + ']'

                # if partner_obj.fantasia and
                #  partner_obj.fantasia.upper() != partner_obj.nome.upper():
                # if partner_obj.razao_social:
                # if partner_obj.razao_social.upper()
                # != partner_obj.fantasia.upper():
                # nome += ' [' + partner_obj.fantasia + ']'

                # else:
                # nome += ' [' + partner_obj.fantasia + ']'

                # res.append((partner_obj.id, nome))
                # else:
                # res.append((partner_obj.id, ''))

                # return res

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
                ('razao_social', 'ilike', name),
                '|',
                ('fantasia', 'ilike', name),
                '|',
                ('cnpj_cpf', 'ilike', mascara(name, '  .   .   /    -  ')),
                ('cnpj_cpf', 'ilike', mascara(name, '   .   .   -  ')),
            ]

        return super(Participante, self).name_search(name=name, args=args,
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
                raise ValidationError('CNPJ/CPF inválido')

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
            raise ValidationError('CNPJ/CPF já existe no cadastro!')

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
                raise ValidationError('Telefone fixo inválido!')

            valores['fone'] = formata_fone(self.fone)

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (
                    not valida_fone_fixo(self.fone_comercial)) and (
                    not valida_fone_celular(self.fone_comercial)):
                raise ValidationError('Telefone comercial inválido!')

            valores['fone_comercial'] = formata_fone(self.fone_comercial)

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (
                    not valida_fone_celular(self.celular)):
                raise ValidationError('Celular inválido!')

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
            raise ValidationError('CEP inválido!')

        valores['cep'] = cep[:5] + '-' + cep[5:]

        return res

    @api.constrains('cep')
    def constrains_cep(self):
        self._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        for participante in self:
            participante._valida_cep()

    def _valida_ie(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.suframa:
            if not valida_inscricao_estadual(self.suframa, 'SUFRAMA'):
                raise ValidationError('Inscrição na SUFRAMA inválida!')

            valores['suframa'] = formata_inscricao_estadual(self.suframa,
                                                            'SUFRAMA')

        if self.ie:
            if self.contribuinte == '2' or self.contribuinte == '3':
                valores['ie'] = ''

            else:
                if not self.municipio_id:
                    raise ValidationError(
                        """Para validação da inscrição estadual é preciso
                        informar o município!""")

                if self.ie.strip().upper()[
                   :6] == 'ISENTO' or self.ie.strip().upper()[:6] == 'ISENTA':
                    raise ValidationError(
                        'Inscrição estadual inválida para contribuinte!')

                if not valida_inscricao_estadual(
                        self.ie, self.municipio_id.estado_id.uf):
                    raise ValidationError('Inscrição estadual inválida!')

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
                    raise ValidationError('Email %s inválido!' % e.strip())

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
                    raise ValidationError('Email %s inválido!' % e.strip())

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
        res = super(Participante, self).fields_view_get(view_id=view_id,
                                                        view_type=view_type,
                                                        toolbar=toolbar,
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

        if self.nome:
            valores['nome'] = primeira_maiuscula(self.nome)

        if self.razao_social:
            valores['razao_social'] = primeira_maiuscula(self.razao_social)

        if self.fantasia:
            valores['fantasia'] = primeira_maiuscula(self.fantasia)

        if self.endereco:
            valores['endereco'] = primeira_maiuscula(self.endereco)

        if self.bairro:
            valores['bairro'] = primeira_maiuscula(self.bairro)

        if self.cidade:
            valores['cidade'] = primeira_maiuscula(self.cidade)

        if self.profissao:
            valores['profissao'] = primeira_maiuscula(self.profissao)

        return res

    @api.onchange('regime_tributario')
    def onchange_regime_tributario(self):
        res = {}
        valores = {}
        res['value'] = valores

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_SIMPLES').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES_EXCESSO:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL:
            valores['al_pis_cofins_id'] = self.env.ref(
                'sped.ALIQUOTA_PIS_COFINS_LUCRO_REAL').id

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

        if not self.partner_id.lang:
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

        if 'lang' not in dados:
            dados['lang'] = 'pt_BR'

        if 'tz' not in dados:
            dados['tz'] = 'America/Sao_Paulo'
        participante = super(Participante, self).create(dados)
        participante.sync_to_partner()

        return participante

    @api.multi
    def write(self, dados):
        if 'nome' in dados:
            dados['name'] = dados['nome']

        res = super(Participante, self).write(dados)
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
