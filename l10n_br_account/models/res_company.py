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
        'l10n_br_account.fiscal.document',
        'Documento Fiscal')
    document_serie_service_id = fields.Many2one(
        'l10n_br_account.document.serie', u'Série Fiscais para Serviço',
        domain="[('company_id', '=', active_id),('active','=',True),"
        "('fiscal_type','=','service')]")
    annual_revenue = fields.Float(
        'Faturamento Anual', required=True,
        digits_compute=dp.get_precision('Account'), default=0.00,
        help="Faturamento Bruto dos últimos 12 meses")
    fiscal_type = fields.Selection(
        COMPANY_FISCAL_TYPE, 'Regime Tributário', required=True,
        default=COMPANY_FISCAL_TYPE_DEFAULT)
    cnae_main_id = fields.Many2one(
        'l10n_br_account.cnae', 'CNAE Primário')
    cnae_secondary_ids = fields.Many2many(
        'l10n_br_account.cnae', 'res_company_l10n_br_account_cnae',
        'company_id', 'cnae_id', 'CNAE Segundários')
    ecnpj_a1_file = fields.Binary('Arquivo e-CNPJ A1')
    ecnpj_a1_password = fields.Char('Senha e-CNPJ A1', size=64)
    fiscal_rule_parent_id = fields.Many2one(
        'account.fiscal.position.rule', u'Conjunto de Regras Fiscais',
        domain="[('parent_id', '=', False)]")
    ipbt_token = fields.Char(string=u'IPBT Token')
    ibpt_update_days = fields.Integer(string=u'IPBT Token')
