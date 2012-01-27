# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel                 #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU General Public License for more details.                                   #
#                                                                               #
#You should have received a copy of the GNU General Public License              #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

import re
import string

from osv import osv, fields

##############################################################################
# Parceiro Personalizado
##############################################################################
class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'tipo_pessoa': fields.selection([('F', 'Física'), ('J', 'Jurídica')], 'Tipo de pessoa', required=True),
        'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
        'inscr_est': fields.char('Inscr. Estadual', size=16),
        'inscr_mun': fields.char('Inscr. Municipal', size=18),
        'suframa': fields.char('Suframa', size=18),
        'legal_name' : fields.char('Razão Social', size=128, help="nome utilizado em documentos fiscais"),
    }

    _defaults = {
        'tipo_pessoa': lambda *a: 'J',
    }

    def _check_cnpj_cpf(self, cr, uid, ids):
        
        for partner in self.browse(cr, uid, ids):
            if not partner.cnpj_cpf:
                return True
    
            if partner.tipo_pessoa == 'J':
                return self.validate_cnpj(partner.cnpj_cpf)
            elif partner.tipo_pessoa == 'F':
                return self.validate_cpf(partner.cnpj_cpf)

        return False

    def validate_cnpj(self, cnpj):
        # Limpando o cnpj
        if not cnpj.isdigit():
            import re
            cnpj = re.sub('[^0-9]', '', cnpj)
           
        # verificando o tamano do  cnpj
        if len(cnpj) != 14:
            return False
            
        # Pega apenas os 12 primeiros dígitos do CNPJ e gera os 2 dígitos que faltam
        cnpj= map(int, cnpj)
        novo = cnpj[:12]

        prod = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        while len(novo) < 14:
            r = sum([x*y for (x, y) in zip(novo, prod)]) % 11
            if r > 1:
                f = 11 - r
            else:
                f = 0
            novo.append(f)
            prod.insert(0, 6)

        # Se o número gerado coincidir com o número original, é válido
        if novo == cnpj:
            return True
            
        return False
    
    def validate_cpf(self, cpf):           
        if not cpf.isdigit():
            import re
            cpf = re.sub('[^0-9]', '', cpf)

        if len(cpf) != 11:
            return False

        # Pega apenas os 9 primeiros dígitos do CPF e gera os 2 dígitos que faltam
        cpf = map(int, cpf)
        novo = cpf[:9]

        while len(novo) < 11:
            r = sum([(len(novo)+1-i)*v for i,v in enumerate(novo)]) % 11

            if r > 1:
                f = 11 - r
            else:
                f = 0
            novo.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if novo == cpf:
            return True
            
        return False

    _constraints = [
                    (_check_cnpj_cpf, 'CNPJ/CPF invalido!', ['cnpj_cpf'])
    ]
    
    _sql_constraints = [
                    ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)', 'Já existe um parceiro cadastrado com este CPF/CNPJ !')
    ]

    def on_change_mask_cnpj_cpf(self, cr, uid, ids, tipo_pessoa, cnpj_cpf):
        if not cnpj_cpf or not tipo_pessoa:
            return {}

        import re
        val = re.sub('[^0-9]', '', cnpj_cpf)

        if tipo_pessoa == 'J' and len(val) == 14:            
            cnpj_cpf = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
        
        elif tipo_pessoa == 'F' and len(val) == 11:
            cnpj_cpf = "%s.%s.%s-%s" % (val[0:3], val[3:6], val[6:9], val[9:11])
        
        return {'value': {'tipo_pessoa': tipo_pessoa, 'cnpj_cpf': cnpj_cpf}}
    
    def zip_search(self, cr, uid, ids, context={}):
        return True    
    
res_partner()

##############################################################################
# Contato do Parceiro Personalizado
##############################################################################
class res_partner_address(osv.osv):
    _inherit = 'res.partner.address'
    _columns = {
	'l10n_br_city_id': fields.many2one('l10n_br_base.city', 'Municipio', domain="[('state_id','=',state_id)]"),
    'district': fields.char('Bairro', size=32),
    'number': fields.char('Número', size=10),
    }

    def onchange_l10n_br_city_id(self, cr, uid, ids, l10n_br_city_id):

        result = {'value': {'city': False, 'l10n_br_city_id': False}}

        if not l10n_br_city_id:
            return result

        obj_city = self.pool.get('l10n_br_base.city').read(cr, uid, l10n_br_city_id, ['name','id'])

        if obj_city:
            result['value']['city'] = obj_city['name']
            result['value']['l10n_br_city_id'] = obj_city['id']

        return result
    
    def onchange_mask_zip(self, cr, uid, ids, zip):
        
        result = {'value': {'zip': False}}
        
        if not zip:
            return result

        val = re.sub('[^0-9]', '', zip)

        if len(val) == 8:
            zip = "%s-%s" % (val[0:5], val[5:8])
            result['value']['zip'] = zip
        return result

    def zip_search(self, cr, uid, ids, context=None):
        
        result = {
                  'street': False, 
                  'l10n_br_city_id': False, 
                  'city': False, 
                  'state_id': False, 
                  'country_id': False, 
                  'zip': False
                  }

        obj_zip = self.pool.get('l10n_br_base.zip')
        
        for res_partner_address in self.browse(cr, uid, ids):
            
            domain = []
            if res_partner_address.zip:
                zip = re.sub('[^0-9]', '', res_partner_address.zip or '')
                domain.append(('code','=',zip))
            else:
                domain.append(('street','=',res_partner_address.street))
                domain.append(('district','=',res_partner_address.district))
                domain.append(('country_id','=',res_partner_address.country_id.id))
                domain.append(('state_id','=',res_partner_address.state_id.id))
                domain.append(('l10n_br_city_id','=',res_partner_address.l10n_br_city_id.id))
            
            zip_id = obj_zip.search(cr, uid, domain)

            if not len(zip_id) == 1:

                context.update({
                                'zip': res_partner_address.zip,
                                'street': res_partner_address.street,
                                'district': res_partner_address.district,
                                'country_id': res_partner_address.country_id.id,
                                'state_id': res_partner_address.state_id.id,
                                'l10n_br_city_id': res_partner_address.l10n_br_city_id.id,
                                'address_id': ids,
                                'object_name': self._name,
                                })

                result = {
                        'name': 'Zip Search',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'l10n_br_base.zip.search',
                        'view_id': False,
                        'context': context,
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'nodestroy': True,
                        }
                return result

            zip_read = obj_zip.read(cr, uid, zip_id, [
                                                      'street_type', 
                                                      'street','district', 
                                                      'code',
                                                      'l10n_br_city_id', 
                                                      'city', 'state_id', 
                                                      'country_id'], context=context)[0]

            zip = re.sub('[^0-9]', '', zip_read['code'] or '')
            if len(zip) == 8:
                zip = '%s-%s' % (zip[0:5], zip[5:8])
            
            result['street'] = ((zip_read['street_type'] or '') + ' ' + (zip_read['street'] or ''))
            result['district'] = zip_read['district']
            result['zip'] = zip
            result['l10n_br_city_id'] = zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][0] or False
            result['city'] = zip_read['l10n_br_city_id'] and zip_read['l10n_br_city_id'][1] or ''
            result['state_id'] = zip_read['state_id'] and zip_read['state_id'][0] or False
            result['country_id'] = zip_read['country_id'] and zip_read['country_id'][0] or False
            self.write(cr, uid, res_partner_address.id, result)
            return False

res_partner_address()

class res_partner_bank(osv.osv):
    '''Bank Accounts'''
    _inherit = 'res.partner.bank'

    _columns = {
                'acc_number': fields.char('Account Number', size=64, required=False),
                'bank': fields.many2one('res.bank', 'Bank', required=False),
                'acc_number_dig': fields.char("Digito Conta", size=8),
                'bra_number': fields.char("Agência", size=8),
                'bra_number_dig': fields.char("Dígito Agência", size=8),
               }

res_partner_bank()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
