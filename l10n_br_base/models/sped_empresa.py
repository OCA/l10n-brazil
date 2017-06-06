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
from ..constante_tributaria import (
    AMBIENTE_NFE,
    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_LUCRO_REAL,
    REGIME_TRIBUTARIO_SIMPLES,
    REGIME_TRIBUTARIO_SIMPLES_EXCESSO,
    TIPO_EMISSAO_NFE,
)


import logging

_logger = logging.getLogger(__name__)


try:
    from email_validator import validate_email

    from pybrasil.base import mascara, primeira_maiuscula
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


class SpedEmpresa(models.Model):
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

        if not self.cnpj_cpf:
            return res

        cnpj_cpf = limpa_formatacao(self.cnpj_cpf or '')

        if cnpj_cpf[:2] != 'EX':
            if not valida_cnpj(cnpj_cpf) and not valida_cpf(cnpj_cpf):
                raise ValidationError(_(u'CNPJ/CPF inválido'))

        if len(cnpj_cpf) == 14:
            valores.update(cnpj_cpf=formata_cnpj(cnpj_cpf))
            valores.update(tipo_pessoa='J')
            valores.update(regime_tributario='1')
        else:
            valores.update(cnpj_cpf=formata_cpf(cnpj_cpf))
            valores.update(tipo_pessoa='F')
            valores.update(regime_tributario='3')

        if cnpj_cpf[:2] == 'EX':
            valores.update(tipo_pessoa='E')
            valores.update(regime_tributario='3')

        if self.id:
            cnpj_ids = self.search([
                ('cnpj_cpf', '=', cnpj_cpf),
                ('id', '!=', self.id),
                ('eh_empresa', '=', False),
                ('eh_grupo', '=', False)
            ])
        else:
            cnpj_ids = self.search([
                ('cnpj_cpf', '=', cnpj_cpf),
                ('eh_empresa', '=', False),
                ('eh_grupo', '=', False)
            ])

        if len(cnpj_ids) > 0:
            raise ValidationError(_(u'CNPJ/CPF já existe no cadastro!'))
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

        if self.fone:
            if (not valida_fone_internacional(self.fone)) and (
                    not valida_fone_fixo(self.fone)):
                raise ValidationError(_(u'Telefone fixo inválido!'))

            valores.update(fone=formata_fone(self.fone))

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (
                    not valida_fone_fixo(self.fone_comercial)) and (
                    not valida_fone_celular(self.fone_comercial)):
                raise ValidationError(_(u'Telefone comercial inválido!'))

            valores.update(fone_comercial=formata_fone(self.fone_comercial))

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (
                    not valida_fone_celular(self.celular)):
                raise ValidationError(_(u'Celular inválido!'))

            valores.update(celular=formata_fone(self.celular))

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

        if not self.cep:
            return res

        cep = limpa_formatacao(self.cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise ValidationError('CEP inválido!')

        valores.update(cep=cep[:5] + '-' + cep[5:])

        return res

    @api.constrains('cep')
    def constrains_cep(self):
        for empresa in self:
            empresa._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        return self._valida_cep()

    def _valida_ie(self):
        self.ensure_one()

        valores = {}
        res = {'value': valores}

        if self.suframa:
            if not valida_inscricao_estadual(self.suframa, 'SUFRAMA'):
                raise ValidationError('Inscrição na SUFRAMA inválida!')

            valores.update(suframa=formata_inscricao_estadual(
                self.suframa, 'SUFRAMA'))

        if self.ie:
            if self.contribuinte == '2' or self.contribuinte == '3':
                valores.update(ie='')

            else:
                if not self.municipio_id:
                    raise ValidationError(
                        '''Para validação da inscrição estadual é preciso
                        informar o município!''')

                if (self.ie.strip().upper()[:6] == 'ISENTO' or
                        self.ie.strip().upper()[:6] == 'ISENTA'):
                    raise ValidationError(
                        'Inscrição estadual inválida para contribuinte!')

                if not valida_inscricao_estadual(
                        self.ie, self.municipio_id.estado_id.uf):
                    raise ValidationError('Inscrição estadual inválida!')

                valores.update(
                    ie=formata_inscricao_estadual(
                        self.ie, self.municipio_id.estado_id.uf))

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

            valores.update(email=','.join(emails_validos))

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

            valores.update(email_nfe=','.join(emails_validos))

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
        valores = {}
        res = {'value': valores}

        if self.municipio_id and self.municipio_id.cep_unico:
            valores.update(cep=self.municipio_id.cep_unico)

        return res

    @api.onchange('nome', 'razao_social', 'fantasia', 'endereco',
                  'bairro', 'cidade', 'profissao')
    def onchange_nome(self):
        valores = {}
        res = {'value': valores}

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

        return res

    def prepare_sync_to_company(self):
        """

        :return:
        """
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
        """ Returns the default company (usually the user's company).
        The 'object' and 'field' arguments are ignored but left here for
        backward compatibility and potential override.
        """
        company = self.env['res.users']._get_company()

        if company.partner_id.sped_empresa_id:
            return company.partner_id.sped_empresa_id
        else:
            return False
