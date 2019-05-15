# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields
from odoo.addons import decimal_precision as dp

COMPANY_FISCAL_TYPE = [
    ('1', 'Simples Nacional'),
    ('2', 'Simples Nacional – excesso de sublimite de receita bruta'),
    ('3', 'Regime Normal')
]

COMPANY_FISCAL_TYPE_DEFAULT = '3'


class ResCompany(models.Model):
    _inherit = 'res.company'

    service_invoice_id = fields.Many2one(
        comodel_name='l10n_br_account.fiscal.document',
        string=u'Documento Fiscal'
    )
    document_serie_service_id = fields.Many2one(
        comodel_name='l10n_br_account.document.serie',
        string=u'Série Fiscais para Serviço',
        domain="[('company_id', '=', active_id), ('active', '=', True),"
               "('fiscal_type', '=', 'service')]"
    )
    annual_revenue = fields.Float(
        string=u'Faturamento Anual',
        required=True,
        digits=dp.get_precision('Account'),
        default=0.00,
        help=u"Faturamento Bruto dos últimos 12 meses"
    )
    fiscal_type = fields.Selection(
        selection=COMPANY_FISCAL_TYPE,
        string=u'Regime Tributário',
        required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT
    )
    cnae_main_id = fields.Many2one(
        comodel_name='l10n_br_account.cnae',
        string=u'CNAE Primário'
    )
    cnae_secondary_ids = fields.Many2many(
        comodel_name='l10n_br_account.cnae',
        relation='res_company_l10n_br_account_cnae',
        column1='company_id',
        column2='cnae_id',
        string=u'CNAE Segundários'
    )
    ecnpj_a1_file = fields.Binary(
        string=u'Arquivo e-CNPJ A1'
    )
    ecnpj_a1_password = fields.Char(
        string=u'Senha e-CNPJ A1',
        size=64
    )
    fiscal_rule_parent_id = fields.Many2one(
        comodel_name='account.fiscal.position.rule',
        string=u'Conjunto de Regras Fiscais',
    )
    ipbt_token = fields.Char(
        string=u'IPBT Token'
    )
    ibpt_update_days = fields.Integer(
        string=u'Quantidade de dias para Atualizar',
    )
