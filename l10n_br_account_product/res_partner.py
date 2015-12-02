# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################


from openerp.osv import orm, fields

FISCAL_POSITION_COLUMNS = {
    'cfop_id': fields.many2one('l10n_br_account_product.cfop', 'CFOP'),
}

class ResPartner(orm.Model):
    _inherit = 'res.partner'
    
    _columns = {
        'is_carrier': fields.boolean("Transportadora?", 
                                     help="O parceiro é uma transportadora?")
    }

class AccountFiscalPositionTemplate(orm.Model):
    _inherit = 'account.fiscal.position.template'
    _columns = FISCAL_POSITION_COLUMNS


class AccountFiscalPosition(orm.Model):
    _inherit = 'account.fiscal.position'
    _columns = FISCAL_POSITION_COLUMNS

    #TODO - Refatorar para trocar os impostos
    def map_tax_code(self, cr, uid, product_id, fiscal_position,
                     company_id=False, tax_ids=False, context=None):

        if not context:
            context = {}

        result = {}
        if tax_ids:

            product = self.pool.get('product.product').browse(
                cr, uid, product_id, context=context)

            fclassificaion = product.ncm_id

            if context.get('type_tax_use') == 'sale':

                if fclassificaion:
                    tax_sale_ids = fclassificaion.sale_tax_definition_line
                    for tax_def in tax_sale_ids:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                            result.update({tax_def.tax_id.domain:
                                           tax_def.tax_code_id.id})

                if company_id:
                    company = self.pool.get('res.company').browse(
                        cr, uid, company_id, context=context)

                    company_tax_def = company.product_tax_definition_line

                    for tax_def in company_tax_def:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                                result.update({tax_def.tax_id.domain:
                                               tax_def.tax_code_id.id})

            if context.get('type_tax_use') == 'purchase':

                if fclassificaion:
                    tax_purchase_ids = fclassificaion.purchase_tax_definition_line
                    for tax_def in tax_purchase_ids:
                        if tax_def.tax_id.id in tax_ids and tax_def.tax_code_id:
                            result.update({tax_def.tax_id.domain:
                                           tax_def.tax_code_id.id})

            if fiscal_position:
                for fp_tax in fiscal_position.tax_ids:
                    if fp_tax.tax_dest_id:
                        if fp_tax.tax_dest_id.id in tax_ids and fp_tax.tax_code_dest_id:
                            result.update({fp_tax.tax_dest_id.domain:
                                           fp_tax.tax_code_dest_id.id})
                    if not fp_tax.tax_dest_id and fp_tax.tax_code_src_id and \
                    fp_tax.tax_code_dest_id:
                        result.update({fp_tax.tax_code_src_id.domain:
                                       fp_tax.tax_code_dest_id.id})

        return result

