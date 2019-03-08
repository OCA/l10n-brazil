# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class L10nBrAccountPartnerFiscalType(models.Model):
    _name = 'l10n_br_account.partner.fiscal.type'
    _description = 'Tipo Fiscal de Parceiros'

    code = fields.Char(
        string=u'Código',
        size=16,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=64)

    is_company = fields.Boolean(
        string=u'Pessoa Jurídica?')

    default = fields.Boolean(
        string=u'Tipo Fiscal Padrão',
        default=True)

    icms = fields.Boolean(
        string=u'Recupera ICMS')

    ipi = fields.Boolean(
        string=u'Recupera IPI')

    @api.constrains('default', 'is_company')
    def _check_default(self):
        for fiscal_type in self:
            if len(fiscal_type.search([
                ('default', '=', 'True'),
                ('is_company', '=', fiscal_type.is_company)
            ])) > 1:
                raise ValidationError(
                    _(u'Mantenha apenas um tipo fiscal padrão'
                      u' para Pessoa Física ou para Pessoa Jurídica!'))
            return True


class L10nBrAccountPartnerSpecialFiscalType(models.Model):
    _name = 'l10n_br_account.partner.special.fiscal.type'
    _description = 'Regime especial do parceiro'

    name = fields.Char(
        string=u'Nome',
        size=20)
