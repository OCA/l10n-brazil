# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# Copyright 2017 KMEE
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .sped_base import SpedBase
from ..constante_tributaria import *


import logging

_logger = logging.getLogger(__name__)


try:
    from email_validator import validate_email

    from pybrasil.base import mascara, primeira_maiuscula
    from pybrasil.data import parse_datetime, dia_util_pagamento, \
        data_hora_horario_brasilia
    from pybrasil.inscricao import (
        formata_cnpj, formata_cpf, limpa_formatacao,
        formata_inscricao_estadual, valida_cnpj, valida_cpf,
        valida_inscricao_estadual
    )
    from pybrasil.telefone import (
        formata_fone, valida_fone_fixo, valida_fone_celular,
        valida_fone_internacional
    )

except (ImportError, IOError) as err:
    _logger.debug(err)


class SpedEmpresa(SpedBase, models.Model):
    _name = b'sped.empresa'
    _description = 'Empresas e filiais'
    _inherits = {'sped.participante': 'participante_id'} # , 'res.company': 'company_id'}
    _rec_name = 'nome'
    _order = 'nome, cnpj_cpf'

    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Participante original',
        ondelete='restrict',
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company original',
        ondelete='restrict',
        # required=True
    )
    eh_empresa = fields.Boolean(
        default=True,
    )

    @api.multi
    def name_get(self):
        res = []

        for empresa in self:
            nome = empresa.nome

            if empresa.razao_social:
                if empresa.nome.strip().upper() != \
                    empresa.razao_social.strip().upper():
                    nome += ' - '
                    nome += empresa.razao_social

            if empresa.cnpj_cpf:
                nome += ' ['
                nome += empresa.cnpj_cpf
                nome += '] '

            res.append((empresa.id, nome))

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
            empresas = self.search(args, limit=limit)
            return empresas.name_get()

        return super(SpedEmpresa, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    def _valida_cnpj_cpf(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if not self.cnpj_cpf or 'valida_cnpj_cpf' in self.env.context:
            return res

        cnpj_cpf = limpa_formatacao(self.cnpj_cpf or '')

        if cnpj_cpf[:2] != 'EX':
            if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                raise ValidationError(_('CNPJ/CPF inválido'))

        if len(cnpj_cpf) == 14:
            cnpj_cpf = formata_cnpj(cnpj_cpf)
            valores['cnpj_cpf'] = cnpj_cpf
            if not self.tipo_pessoa:
                valores['tipo_pessoa'] = TIPO_PESSOA_JURIDICA
            if not self.regime_tributario:
                valores['regime_tributario'] = REGIME_TRIBUTARIO_SIMPLES
            if not self.contribuinte:
                valores['contribuinte'] = INDICADOR_IE_DESTINATARIO_ISENTO

        else:
            cnpj_cpf = formata_cpf(cnpj_cpf)
            valores['cnpj_cpf'] = cnpj_cpf
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
            raise ValidationError(_('CNPJ/CPF já existe no cadastro!'))

        self.with_context(valida_cnpj_cpf=True).update(valores)

        return res

    @api.constrains('cnpj_cpf')
    def constrains_cnpj_cpf(self):
        for empresa in self:
            empresa._valida_cnpj_cpf()

    @api.onchange('cnpj_cpf')
    def onchange_cnpj_cpf(self):
        return self._valida_cnpj_cpf()

    def _valida_fone(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if 'valida_fone' in self.env.context:
            return res

        if self.fone:
            if (not valida_fone_internacional(self.fone)) and (
                    not valida_fone_fixo(self.fone)):
                raise ValidationError(_('Telefone fixo inválido!'))

            valores['fone'] = formata_fone(self.fone)

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (
                    not valida_fone_fixo(self.fone_comercial)) and (
                    not valida_fone_celular(self.fone_comercial)):
                raise ValidationError(_('Telefone comercial inválido!'))

            valores['fone_comercial'] = formata_fone(self.fone_comercial)

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (
                    not valida_fone_celular(self.celular)):
                raise ValidationError(_('Celular inválido!'))

            valores['celular'] = formata_fone(self.celular)

        self.with_context(valida_fone=True).update(valores)

        return res

    @api.constrains('fone', 'celular', 'fone_comercial')
    def constrains_fone(self):
        for empresa in self:
            empresa._valida_fone()

    @api.onchange('fone', 'celular', 'fone_comercial')
    def onchange_fone(self):
        return self._valida_fone()

    def _valida_cep(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if not self.cep or 'valida_cep' in self.env.context:
            return res

        cep = limpa_formatacao(self.cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise ValidationError(_('CEP inválido!'))

        valores['cep'] = cep[:5] + '-' + cep[5:]

        self.with_context(valida_cep=True).update(valores)

        return res

    @api.constrains('cep')
    def constrains_cep(self):
        for empresa in self:
            empresa._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        return self._valida_cep()

    def _valida_suframa(self, valores):
        self.ensure_one()

        if not valida_inscricao_estadual(self.suframa, 'SUFRAMA'):
            raise ValidationError(_('Inscrição na SUFRAMA inválida!'))

        valores['suframa'] = \
            formata_inscricao_estadual(self.suframa, 'SUFRAMA')

    def _valida_ie_estadual(self, valores):
        self.ensure_one()

        if not valida_inscricao_estadual(self.ie,
            self.municipio_id.estado_id.uf):
            raise ValidationError(_('Inscrição estadual inválida!'))

        valores['ie'] = \
            formata_inscricao_estadual(self.ie, self.municipio_id.estado_id.uf)

    def _valida_ie(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if 'valida_ie' in self.env.context:
            return res

        if self.suframa:
            self._valida_suframa(valores)

        #
        # Na importação de dados, validamos e detectamos o campo
        # contribuinte a partir da inscrição estadual, e não o contrário
        #
        if 'import_file' in self.env.context:
            #
            # Sem inscrição estadual, presumimos que o participante não é
            # contribuinte, que é o caso mais comum; é muito raro na verdade
            # que seja isento
            #
            if not self.ie:
                valores['contribuinte'] = \
                    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE

            elif self.ie.strip().upper()[:6] == 'ISENTO' or \
                self.ie.strip().upper()[:6] == 'ISENTA':
                valores['contribuinte'] = INDICADOR_IE_DESTINATARIO_ISENTO

            else:
                if not self.municipio_id:
                    raise ValidationError(_(
                        '''Para validação da inscrição estadual é preciso
                        informar o município!'''))

                self._valida_ie_estadual(valores)
                valores['contribuinte'] = \
                    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE

        elif self.ie:
            if self.contribuinte == INDICADOR_IE_DESTINATARIO_ISENTO or \
                self.contribuinte == \
                    INDICADOR_IE_DESTINATARIO_NAO_CONTRIBUINTE:
                valores['ie'] = ''
            else:
                if not self.municipio_id:
                    raise ValidationError(_(
                        '''Para validação da inscrição estadual é preciso
                        informar o município!'''))

                if self.ie.strip().upper()[:6] == 'ISENTO' or \
                    self.ie.strip().upper()[:6] == 'ISENTA':
                    raise ValidationError(
                        _('Inscrição estadual inválida para contribuinte!'))

                self._valida_ie_estadual(valores)

        self.with_context(valida_ie=True).update(valores)

        return res

    @api.constrains('suframa', 'ie', 'municipio_id', 'contribuinte')
    def constrains_ie(self):
        for empresa in self:
            empresa._valida_ie()

    @api.onchange('suframa', 'ie', 'municipio_id', 'contribuinte')
    def onchange_ie(self):
        return self._valida_ie()

    def _valida_email(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if 'valida_email' in self.env.context:
            return res

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
                    raise ValidationError(_('Email %s inválido!' % e.strip()))

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
                        _('Email %s inválido!' % e.strip()))

            valores['email_nfe'] = ','.join(emails_validos)

        self.with_context(valida_email=True).update(valores)

        return res

    @api.constrains('email', 'email_nfe')
    def constrains_email(self):
        for empresa in self:
            empresa._valida_email()

    @api.onchange('email', 'email_nfe')
    def onchange_email(self):
        return self._valida_email()

    @api.onchange('municipio_id')
    def onchange_municipio_id(self):
        if self.municipio_id and self.municipio_id.cep_unico:
            self.cep = self.municipio_id.cep_unico

    @api.onchange('nome', 'razao_social', 'fantasia', 'endereco',
                  'bairro', 'cidade', 'profissao')
    def onchange_nome(self):
        pass
        # if self.nome:
        #     valores.update(nome=primeira_maiuscula(self.nome))
        #
        # if self.razao_social:
        #     valores.update(razao_social=primeira_maiuscula(self.razao_social))
        #
        # if self.fantasia:
        #     valores.update(fantasia=primeira_maiuscula(self.fantasia))
        #
        # if self.endereco:
        #     valores.update(endereco=primeira_maiuscula(self.endereco))
        #
        # if self.bairro:
        #     valores.update(bairro=primeira_maiuscula(self.bairro))
        #
        # if self.cidade:
        #     valores.update(cidade=primeira_maiuscula(self.cidade))
        #
        # if self.profissao:
        #     valores.update(profissao=primeira_maiuscula(self.profissao))

    def prepare_sync_to_company(self):
        '''

        :return:
        '''
        self.ensure_one()

        dados = {
            'name': self.nome,
            'phone': self.partner_id.phone,
            'email': self.partner_id.email,
        }

        if self.contribuinte == INDICADOR_IE_DESTINATARIO_CONTRIBUINTE:
            registry = 'BR-'
            registry += self.municipio_id.estado_id.uf + '-'
            registry += self.ie
            dados['company_registry'] = registry

        if not self.company_id:
            dados.update(partner_id=self.partner_id.id)
            dados.update(rml_paper_format='a4')
            dados.update(paperformat_id=self.env.ref(
                'report.paperformat_euro').id
                         )
        dados.update(currency_id=self.env.ref('base.BRL').id)

        return dados

    @api.multi
    def sync_to_company(self):
        for empresa in self:
            if not empresa.partner_id.sped_empresa_id:
                empresa.partner_id.write({'sped_empresa_id': self.id})

            dados = empresa.prepare_sync_to_company()

            if empresa.company_id:
                empresa.company_id.write(dados)

            else:
                # FIXME: company = self.env['res.company'].create(dados)
                self.env['res.company'].create(dados)

    @api.model
    def create(self, dados):
        if 'razao_social' in dados and not dados['razao_social']:
            dados['razao_social'] = dados['nome']

        dados['name'] = dados['nome']

        if 'lang' not in dados:
            dados['lang'] = 'pt_BR'

        if 'tz' not in dados:
            dados['tz'] = 'America/Sao_Paulo'

        #
        # Resolve o default do partner vinculado ao company
        # nem pergunte...
        #
        if 'company_id' not in dados or not dados['company_id']:
            company = self.env['res.company'].create(dados)
            dados['company_id'] = company.id
            dados['partner_id'] = company.partner_id.id

        empresa = super(SpedEmpresa, self).create(dados)
        empresa.sync_to_company()
        return empresa

    @api.multi
    def write(self, dados):
        if 'nome' in dados:
            dados['name'] = dados['nome']

        res = super(SpedEmpresa, self).write(dados)
        self.sync_to_company()
        return res

    @api.onchange('company_id')
    def _onchange_company_id(self):
        valores = {}
        res = {'value': valores}

        valores['partner_id'] = self.company_id.partner_id.id

        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        valores = {}
        res = {'value': valores}

        if self.partner_id.customer:
            valores.update(eh_cliente=True)
        else:
            valores.update(eh_cliente=False)

        if self.partner_id.supplier:
            valores.update(eh_fornecedor=True)
        else:
            valores.update(eh_fornecedor=False)

        if self.partner_id.employee:
            valores.update(eh_funcionario=True)
        else:
            valores.update(eh_funcionario=False)

        if self.partner_id.original_company_id:
            valores.update(eh_empresa=True)
        else:
            valores.update(eh_empresa=False)

        if self.partner_id.original_user_id:
            valores.update(eh_usuario=True)
        else:
            valores.update(eh_usuario=False)

        return res

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _empresa_ativa(self, object=False, field=False):
        ''' Returns the default company (usually the user's company).
        The 'object' and 'field' arguments are ignored but left here for
        backward compatibility and potential override.
        '''
        company = self.env['res.users']._get_company()

        if company.partner_id.sped_empresa_id:
            return company.partner_id.sped_empresa_id
        else:
            return False

    def dia_util(self, data_referencia, antecipa=False):
        self.ensure_one()

        if not data_referencia:
            return data_referencia

        if isinstance(data_referencia, (str, unicode)):
            #
            # Caso venha uma data e hora, assumimos que veio em UTC
            #
            if len(data_referencia) > 10:
                data_referencia = data_hora_horario_brasilia(
                    parse_datetime(data_referencia + ' UTC'))

        data_referencia = parse_datetime(data_referencia)
        estado = self.estado
        municipio = self.cidade

        data_util = dia_util_pagamento(data_referencia, estado, municipio,
                                       antecipa)
        return data_util
