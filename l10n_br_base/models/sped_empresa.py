# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    _description = u'Empresas e filiais'
    _inherits = {'sped.participante': 'participante_id'}
    # _inherit = 'mail.thread'
    # _inherits = 'res.partner'
    _name = 'sped.empresa'
    _rec_name = 'nome'
    _order = 'nome, cnpj_cpf'

    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Participante original',
        ondelete='restrict',
        required=True
    )

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

        return super(Empresa, self).name_search(
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
                raise ValidationError('CNPJ/CPF inválido')

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
            raise ValidationError(u'CNPJ/CPF já existe no cadastro!')

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
                raise ValidationError(u'Telefone fixo inválido!')

            valores.update(fone=formata_fone(self.fone))

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (
                    not valida_fone_fixo(self.fone_comercial)) and (
                    not valida_fone_celular(self.fone_comercial)):
                raise ValidationError(u'Telefone comercial inválido!')

            valores.update(fone_comercial=formata_fone(self.fone_comercial))

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (
                    not valida_fone_celular(self.celular)):
                raise ValidationError(u'Celular inválido!')

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
            raise ValidationError(u'CEP inválido!')

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
                raise ValidationError(u'Inscrição na SUFRAMA inválida!')

            valores.update(suframa=formata_inscricao_estadual(
                self.suframa, 'SUFRAMA'))

        if self.ie:
            if self.contribuinte == '2' or self.contribuinte == '3':
                valores.update(ie='')

            else:
                if not self.municipio_id:
                    raise ValidationError(
                        u"""Para validação da inscrição estadual é preciso
                        informar o município!""")

                if (self.ie.strip().upper()[:6] == 'ISENTO' or
                        self.ie.strip().upper()[:6] == 'ISENTA'):
                    raise ValidationError(
                        u'Inscrição estadual inválida para contribuinte!')

                if not valida_inscricao_estadual(
                        self.ie, self.municipio_id.estado_id.uf):
                    raise ValidationError(u'Inscrição estadual inválida!')

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
                    raise ValidationError(u'Email %s inválido!' % e.strip())

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
                    raise ValidationError(u'Email %s inválido!' % e.strip())

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

        if self.nome:
            valores.update(nome=primeira_maiuscula(self.nome))

        if self.razao_social:
            valores.update(razao_social=primeira_maiuscula(self.razao_social))

        if self.fantasia:
            valores.update(fantasia=primeira_maiuscula(self.fantasia))

        if self.endereco:
            valores.update(endereco=primeira_maiuscula(self.endereco))

        if self.bairro:
            valores.update(bairro=primeira_maiuscula(self.bairro))

        if self.cidade:
            valores.update(cidade=primeira_maiuscula(self.cidade))

        if self.profissao:
            valores.update(profissao=primeira_maiuscula(self.profissao))

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
        empresa = super(Empresa, self).create(dados)
        empresa.sync_to_company()
        return empresa


    @api.multi
    def write(self, dados):
        res = super(Empresa, self).write(dados)
        self.sync_to_company()
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
