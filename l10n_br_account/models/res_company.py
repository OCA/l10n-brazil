# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 - TODAY Renato Lima - Akretion                           #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

from openerp import models, fields
from openerp.addons import decimal_precision as dp

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
    ipbt_token = fields.Char(string='IPBT Token')
