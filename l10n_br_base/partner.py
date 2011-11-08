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

from osv import osv, fields

##############################################################################
# Parceiro Personalizado
##############################################################################
class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'tipo_pessoa': fields.selection([('F', 'Física'), ('J', 'Jurídica')], 'Tipo de pessoa', required=True),
        'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
        'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
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
    
    def _check_ie(self, cr, uid, ids):
        
        for partner in self.browse(cr, uid, ids):
            if not partner.inscr_est:
                return True
            
            if partner.tipo_pessoa == 'J':
                    
                return self.validate_cnpj(partner.inscr_est)

        return False

    def validate_ie_ac(self, inscr_est):
        """ Verificação da Inscrição Estadual-Acre """
        return True
    
    def validate_ie_al(self, inscr_est):
        """ Verificação da Inscrição Estadual-Alagoas """
        return True
    
    def validate_ie_am(self, inscr_est):
        """ Verificação da Inscrição Estadual-Amazonas """
        return True
    
    def validate_ie_ap(self, inscr_est):
        """ Verificação da Inscrição Estadual-Amapá """
        return True
    
    def validate_ie_ba(self, inscr_est):
        """ Verificação da Inscrição Estadual-Bahia """
        return True
    
    def validate_ie_ce(self, inscr_est):
        """ Verificação da Inscrição Estadual-Ceará """
        return True
    
    def validate_ie_df(self, inscr_est):
        """ Verificação da Inscrição Estadual-Distitro Federal """
        return True
    
    def validate_ie_es(self, inscr_est):
        """ Verificação da Inscrição Estadual-Espirito Santo """
        return True
    
    def validate_ie_go(self, inscr_est):
        """ Verificação da Inscrição Estadual-Goiais """
        return True
    
    def validate_ie_ma(self, inscr_est):
        """ Verificação da Inscrição Estadual-Maranhão """
        return True
    
    def validate_ie_mg(self, inscr_est):
        """ Verificação da Inscrição Estadual-Minas Gerais """
        return True
    
    def validate_ie_ms(self, inscr_est):
        """ Verificação da Inscrição Estadual-Mato Grosso do Sul """
        return True
    
    def validate_ie_mt(self, inscr_est):
        """ Verificação da Inscrição Estadual-Mato Grosso """
        return True
    
    def validate_ie_pa(self, inscr_est):
        """ Verificação da Inscrição Estadual-Pará """
        return True
    
    def validate_ie_pb(self, inscr_est):
        """ Verificação da Inscrição Estadual-Paraíba """
        return True
    
    def validate_ie_pe(self, inscr_est):
        """ Verificação da Inscrição Estadual-Pernambuco """
        return True
    
    def validate_ie_pi(self, inscr_est):
        """ Verificação da Inscrição Estadual-Piauí """
        return True
    
    def validate_ie_pr(self, inscr_est):
        """ Verificação da Inscrição Estadual-Paraná """
        return True
    
    def validate_ie_rj(self, inscr_est):
        """ Verificação da Inscrição Estadual-Rio de Janeiro """
        return True
    
    def validate_ie_rn(self, inscr_est):
        """ Verificação da Inscrição Estadual-Rio Grande do Norte """
        return True
    
    def validate_ie_ro(self, inscr_est):
        """ Verificação da Inscrição Estadual-Rondônia """
        return True
    
    def validate_ie_rr(self, inscr_est):
        """ Verificação da Inscrição Estadual-Roraima """
        return True
    
    def validate_ie_rs(self, inscr_est):
        """ Verificação da Inscrição Estadual-Rio Grande do Sul """
        return True
    
    def validate_ie_sc(self, inscr_est):
        """ Verificação da Inscrição Estadual-Santa Catarina """
        return True
    
    def validate_ie_se(self, inscr_est):
        """ Verificação da Inscrição Estadual-Sergipe """
        return True
    
    def validate_ie_sp(self, inscr_est):
        """ Verificação da Inscrição Estadual-São Paulo """
        return True
    
    def validate_ie_to(self, inscr_est):
        """ Verificação da Inscrição Estadual-Tocantins """
        return True
    
    _constraints = [
                    (_check_cnpj_cpf, 'CNPJ/CPF invalido!', ['cnpj_cpf']),
                    (_check_ie, 'Inscrição Estadual invalida!', ['inscr_est'])
    ]
    
    _sql_constraints = [
                    ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)', 'Já existe um parceiro cadastrado com este CPF/CNPJ !'),
                    ('res_partner_inscr_est_uniq', 'unique (inscr_est)', 'Já existe um parceiro cadastrado com esta Inscrição Estadual/RG !')
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

    def on_change_l10n_br_city_id(self, cr, uid, ids, l10n_br_city_id):

        result = {}

        if not l10n_br_city_id:
            return True

        obj_city = self.pool.get('l10n_br_base.city').read(cr, uid, l10n_br_city_id, ['name','id'])

        if obj_city:
            result['city'] = obj_city['name']
            result['l10n_br_city_id'] = obj_city['id']

        return {'value': result}

    def on_change_zip(self, cr, uid, ids, zip):
        
        result = {'value': {'street': None, 'l10n_br_city_id': None, 'city': None, 'state_id': None, 'country_id': None, 'zip': None }}

        if not zip:
            return result
        
        obj_cep = self.pool.get('l10n_br_base.cep').browse(cr, uid, zip)
        
        result['value']['street'] = obj_cep.street_type + ' ' + obj_cep.street
        result['value']['l10n_br_city_id'] = obj_cep.l10n_br_city_id.id
        result['value']['city'] = obj_cep.l10n_br_city_id.name
        result['value']['state_id'] = obj_cep.state_id.id
        result['value']['country_id'] = obj_cep.state_id.country_id.id
        result['value']['zip'] = obj_cep.code
        
        return result

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
