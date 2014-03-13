# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2014  Luis Felipe Mileo - KMEE, www.kmee.com.br               #
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

from .sped.nfe.processing.xml import check_partner
from openerp.osv import orm

class ResPartner(orm.Model):
    _inherit = 'res.partner'

    def sefaz_check(self, cr, uid, ids, context=False):
               
        if context.get('company_id', False):
            company = context['company_id']
        else:
            company = self.pool.get('res.users').browse(cr, uid, uid,
                context=context).company_id
        
        #for partner in self.browse(cr, uid, ids, context):
            
         #   processo = check_partner(company, partner.state_id.code, partner.inscr_est ,partner.cnpj_cpf )      
            #processar xml
        return
    
    def onchange_mask_cnpj_cpf(self, cr, uid, ids, is_company, cnpj_cpf):
        result = super(ResPartner, self).onchange_mask_cnpj_cpf(
            cr, uid, ids, is_company, cnpj_cpf)
        
        context = {}
        
        if cnpj_cpf:
            
            if context.get('company_id', False):
                company = context['company_id']
            else:
                company = self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id
           
        #    processo = check_partner(company, company.partner_id.state_id.code, None , cnpj_cpf )      
        return result

