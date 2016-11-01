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
from .res_partner import *


class Company(models.Model):
    _description = 'Empresas'
    _name = 'res.company'
    _inherit = 'res.company'

    @api.model
    def create(self, dados):
        #
        # Não chamar a criação do company original, pois isso será tratado dentro do partner
        #
        self.clear_caches()
        return super(models.Model, self).create(dados)

    @api.model
    def write(self, dados):
        for empresa in self:
            empresa.partner_id.write({'is_company': True, 'eh_empresa': True})

        return super(Company, self).write(dados)
