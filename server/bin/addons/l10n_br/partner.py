# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields

##############################################################################
# Parceiro Personalizado
##############################################################################
class res_partner(osv.osv):
    _description = 'Parceiro Personalizado'
    _inherit = 'res.partner'
    _columns = {
        'cnpj_cpf': fields.char('CNPJ/CPF',size=16),
        'inscr_est': fields.char('Inscr. Estadual',size=16),
    }
    
    def zip_search(self, cr, uid, ids, context={}):
        return True
    
res_partner()

##############################################################################
# Contato do Parceiro Personalizado
##############################################################################
class res_partner_address(osv.osv):
    _description = 'Parceiro Personalizado'
    _inherit = 'res.partner.address'
    _columns = {
        'number': fields.char('Número',size=10),
        'city_id': fields.many2one('l10n_br.city','Municipio'),
    }

res_partner_address()
