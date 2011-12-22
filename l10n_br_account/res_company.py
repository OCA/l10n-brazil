# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

from osv import osv, fields
import decimal_precision as dp

class res_company(osv.osv):

    _inherit = "res.company"

    _columns = {
                'fiscal_type': fields.selection([('1', 'Simples Nacional'), 
                                                 ('2', 'Simples Nacional – excesso de sublimite de receita bruta'), 
                                                 ('3', 'Regime Normal')], 
                                                'Regime Tributário', required=True),
                'annual_revenue': fields.float('Faturamento Anual', required=True,
                                               digits_compute=dp.get_precision('Account'),
                                               help="Faturamento Bruto dos últimos 12 meses"),
                'document_serie_product_ids': fields.many2many('l10n_br_account.document.serie',
                                                               'res_company_l10n_br_account_document_serie', 'company_id',
                                                               'document_serie_product_id', 'Série de Documentos Fiscais',
                                                               domain="[('company_id', '=', active_id),('active','=',True),    ('fiscal_type','=','product')]"),
                'document_serie_service_id': fields.many2one('l10n_br_account.document.serie', 'Série Fiscais para Serviço',
                                                             domain="[('company_id', '=', active_id),('active','=',True),('fiscal_type','=','service')]" ),
                'cnae_main_id': fields.many2one('l10n_br_account.cnae', 'CNAE Primário' ),
                'cnae_secondary_ids': fields.many2many('l10n_br_account.cnae', 'res_company_l10n_br_account_cnae', 
                                                       'company_id', 'cnae_id', 'CNAE Segundários'),
                'nfe_version': fields.selection([('1.00', '1.00'), ('2.00', '2.00')], 'Versão NFe', required=True),
                'nfe_source_folder': fields.char('Pasta de Origem', size=254),
                'nfe_destination_folder': fields.char('Pasta de Destino', size=254),
                'nfse_version': fields.selection([('1.00', '1.00')], 'Versão NFse', required=True),
                'nfse_source_folder': fields.char('Pasta de Origem', size=254),
                'nfse_destination_folder': fields.char('Pasta de Destino', size=254),
    }

    _defaults = {
                'fiscal_type': '3',
                'nfe_version': '2.00',
                'nfse_version': '1.00',
                'annual_revenue': 0.0,
                }

res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
