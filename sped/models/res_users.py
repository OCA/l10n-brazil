# -*- coding: utf-8 -*-


from __future__ import division, print_function, unicode_literals
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from pybrasil.inscricao import (formata_cnpj, formata_cpf, limpa_formatacao, formata_inscricao_estadual, valida_cnpj, valida_cpf, valida_inscricao_estadual)
from pybrasil.telefone import (formata_fone, valida_fone_fixo, valida_fone_celular, valida_fone_internacional, valida_fone, formata_varios_fones)
from pybrasil.base import mascara
#from integra_rh.models.hr_employee import SEXO, ESTADO_CIVIL
from email_validator import validate_email, EmailNotValidError
from ..constante_tributaria import *


IE_DESTINATARIO = (
    ('1', 'Contribuinte'),
    ('2', 'Isento'),
    ('9', 'Não contribuinte/estrangeiro'),
)


TIPO_PESSOA = (
    ('F', 'Física'),
    ('J', 'Jurídica'),
    ('E', 'Estrangeiro'),
    ('I', 'Indeterminado'),
)


class Users(models.Model):
    _description = 'Usuários'
    _name = 'res.users'
    _inherit = 'res.users'

    def _valida_cnpj_cpf(self):
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
            valores['tipo_pessoa'] = 'J'
            valores['regime_tributario'] = '1'
        else:
            valores['cnpj_cpf'] = formata_cpf(cnpj_cpf)
            valores['tipo_pessoa'] = 'F'
            valores['regime_tributario'] = '3'

        if cnpj_cpf[:2] == 'EX':
            valores['tipo_pessoa'] = 'E'
            valores['regime_tributario'] = '3'

        if self.id:
            cnpj_ids = self.search([('cnpj_cpf', '=', cnpj_cpf), ('id', '!=', self.id), ('eh_empresa', '=', False), ('eh_grupo', '=', False)])
        else:
            cnpj_ids = self.search([('cnpj_cpf', '=', cnpj_cpf), ('eh_empresa', '=', False), ('eh_grupo', '=', False)])

        if len(cnpj_ids) > 0:
            raise ValidationError('CNPJ/CPF já existe no cadastro!')

        return res

    @api.one
    @api.constrains('cnpj_cpf')
    def constrains_cnpj_cpf(self):
        self._valida_cnpj_cpf()

    @api.onchange('cnpj_cpf')
    def onchange_cnpj_cpf(self):
        return self._valida_cnpj_cpf()

    def _valida_fone(self):
        valores = {}
        res = {'value': valores}

        if self.fone:
            if (not valida_fone_internacional(self.fone)) and (not valida_fone_fixo(self.fone)):
                raise ValidationError('Telefone fixo inválido!')

            valores['fone'] = formata_fone(self.fone)

        if self.fone_comercial:
            if (not valida_fone_internacional(self.fone_comercial)) and (not valida_fone_fixo(self.fone_comercial)) and (not valida_fone_celular(self.fone_comercial)):
                raise ValidationError('Telefone comercial inválido!')

            valores['fone_comercial'] = formata_fone(self.fone_comercial)

        if self.celular:
            if (not valida_fone_internacional(self.celular)) and (not valida_fone_celular(self.celular)):
                raise ValidationError('Celular inválido!')

            valores['celular'] = formata_fone(self.celular)

        return res

    @api.one
    @api.constrains('fone', 'celular', 'fone_comercial')
    def constrains_fone(self):
        self._valida_fone()

    @api.onchange('fone', 'celular', 'fone_comercial')
    def onchange_fone(self):
        return self._valida_fone()

    def _valida_cep(self):
        valores = {}
        res = {'value': valores}

        if not self.cep:
            return res

        cep = limpa_formatacao(self.cep)
        if (not cep.isdigit()) or len(cep) != 8:
            raise ValidationError('CEP inválido!')

        valores['cep'] = cep[:5] + '-' + cep[5:]

        return res

    @api.one
    @api.constrains('cep')
    def constrains_cep(self):
        self._valida_cep()

    @api.onchange('cep')
    def onchange_cep(self):
        return self._valida_cep()

    def _valida_ie(self):
        valores = {}
        res = {'value': valores}

        if self.suframa:
            if not valida_inscricao_estadual(suframa, 'SUFRAMA'):
                raise ValidationError('Inscrição na SUFRAMA inválida!')

            valores['suframa'] = formata_inscricao_estadual(self.suframa, 'SUFRAMA')

        if self.ie:
            if self.contribuinte == '2' or self.contribuinte == '3':
                valores['ie'] = ''

            else:
                if not self.municipio_id:
                    raise ValidationError('Para validação da inscrição estadual é preciso informar o município!')

                if self.ie.strip().upper()[:6] == 'ISENTO' or self.ie.strip().upper()[:6] == 'ISENTA':
                    raise ValidationError('Inscrição estadual inválida para contribuinte!')

                if not valida_inscricao_estadual(self.ie, self.municipio_id.estado_id.uf):
                    raise ValidationError('Inscrição estadual inválida!')

                valores['ie'] = formata_inscricao_estadual(self.ie, self.municipio_id.estado_id.uf)

        return res

    @api.one
    @api.constrains('suframa', 'ie', 'municipio_id', 'contribuinte')
    def constrains_ie(self):
        self._valida_ie()

    @api.onchange('suframa', 'ie', 'municipio_id', 'contribuinte')
    def onchange_ie(self):
        return self._valida_ie()

    def _valida_email(self):
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

    @api.one
    @api.constrains('email', 'email_nfe')
    def constrains_email(self):
        self._valida_email()

    @api.onchange('email', 'email_nfe')
    def onchange_email(self):
        return self._valida_email()
