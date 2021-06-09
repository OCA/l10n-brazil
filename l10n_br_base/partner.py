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
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

import re
import string

from osv import osv, fields

class res_partner(osv.osv):

    _inherit = 'res.partner'

    def _get_partner_address(self, cr, uid, ids, context=None):
        result = {}
        for parnter_addr in self.pool.get('res.partner.address').browse(cr, uid, ids, context=context):
            result[parnter_addr.partner_id.id] = True
        return result.keys()

    def _address_default_fs(self, cr, uid, ids, name, arg, context=None):
        
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = {'addr_fs_code': False}
            
            partner_addr = self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['invoice'])
            if partner_addr:
                partner_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [partner_addr['invoice']])[0]
                addr_fs_code = partner_addr_default.state_id and partner_addr_default.state_id.code or ''
                res[partner.id]['addr_fs_code'] = addr_fs_code.lower()
                
        return res

    _columns = {
                'tipo_pessoa': fields.selection([('F', 'Física'), ('J', 'Jurídica')], 'Tipo de pessoa', required=True),
                'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
                'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
                'inscr_mun': fields.char('Inscr. Municipal', size=18),
                'suframa': fields.char('Suframa', size=18),
                'legal_name' : fields.char('Razão Social', size=128, help="nome utilizado em documentos fiscais"),
                'addr_fs_code': fields.function(_address_default_fs, method=True, 
                                                string='Address Federal State Code', 
                                                type="char", size=2, multi='all',
                                                store={'res.partner.address': (_get_partner_address, ['country_id', 'state_id'], 20),}),
                
                }

    _defaults = {
                'tipo_pessoa': lambda *a: 'J',
                }

    def _check_cnpj_cpf(self, cr, uid, ids):

        for partner in self.browse(cr, uid, ids):
            if not partner.cnpj_cpf:
                continue
    
            if partner.tipo_pessoa == 'J':
                if not self._validate_cnpj(partner.cnpj_cpf):
                    return False
            elif partner.tipo_pessoa == 'F':
                if not self._validate_cpf(partner.cnpj_cpf):
                    return False

        return True

    def _validate_cnpj(self, cnpj):
        
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
    
    def _validate_cpf(self, cpf):  
        
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
        """Checks if company register number in field insc_est is valid, 
        this method call others methods because this validation is State wise
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of partner Ids,
        @return: True or False.
        """

        for partner in self.browse(cr, uid, ids):
            
            validate = getattr(self, '_validate_ie_%s' % partner.addr_fs_code, None)

            if not partner.inscr_est or partner.inscr_est == 'ISENTO' or not validate or partner.tipo_pessoa == 'F':
                continue

            if partner.tipo_pessoa == 'J':
                if callable(validate):
                    if not validate(partner.inscr_est):
                        return False

        return True

    def _validate_ie_ac(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Acre
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 13:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '01':
            return False

        # Pega apenas os 11 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:11]

        prod = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        while len(nova_ie) < 13:
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r > 1:
                f = 11 - r
            else:
                f = 0
            nova_ie.append(f)
            prod.insert(0, 5)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_al(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Alagoas
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '24':
            return False

        # verificando o tipo de empresa
        #if not inscr_est[2] in ['0', '3', '5', '7', '8']:
        #    return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = (sum([x*y for (x, y) in zip(nova_ie, prod)]) * 10) % 11
        if r > 9:
            r = 0
        nova_ie.append(r)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
   
    def _validate_ie_am(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Amazonas
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_ap(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Amapá
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '03':
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # define os valores de 'p' e 'd'
        inscr_est_int = int(inscr_est[:8])
        if (inscr_est_int <= 3017000):
            inscr_est_p = 5
            inscr_est_d = 0
        if (inscr_est_int >= 3017001) and (inscr_est_int <= 3019022):
            inscr_est_p = 9
            inscr_est_d = 1
        if (inscr_est_int >= 3019023):
            inscr_est_p = 0
            inscr_est_d = 0

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = (inscr_est_p + sum([x*y for (x, y) in zip(nova_ie, prod)])) % 11
        if r > 1:
            f = 11 - r
        elif r == 1:
            f = 0
        else:
            f = inscr_est_d
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_ba(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Bahia
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if (len(inscr_est) != 8) and (len(inscr_est) != 9):
            return False

        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 8:

            # Pega apenas os 6 primeiros dígitos da inscrição estadual e
            # gera os dígitos verificadores
            nova_ie = inscr_est[:6]

            prod = [7, 6, 5, 4, 3, 2]

            if inscr_est[0] in [0, 1, 2, 3, 4, 5, 8]:
                modulo = 10
            else:
                modulo = 11

            while len(nova_ie) < 8:

                r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % modulo
                if r > 0:
                    f = modulo - r
                else:
                    f = 0

                if len(nova_ie) < 7:
                    nova_ie.append(f)
                else:
                    nova_ie.insert(6, f)

                prod.insert(0, 8)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 9:

            # Pega apenas os 7 primeiros dígitos da inscrição estadual e
            # gera os dígitos verificadores
            nova_ie = inscr_est[:7]

            prod = [8, 7, 6, 5, 4, 3, 2]

            if inscr_est[1] in [0, 1, 2, 3, 4, 5, 8]:
                modulo = 10
            else:
                modulo = 11

            while len(nova_ie) < 9:

                r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % modulo
                if r > 0:
                    f = modulo - r
                else:
                    f = 0

                if len(nova_ie) < 8:
                    nova_ie.append(f)
                else:
                    nova_ie.insert(7, f)

                prod.insert(0, 9)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_ce(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Ceará
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_df(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Distitro Federal
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False._check_ie
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 13:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '07':
            return False

        # Pega apenas os 11 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:11]

        prod = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        while len(nova_ie) < 13:
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r > 1:
                f = 11 - r
            else:
                f = 0
            nova_ie.append(f)
            prod.insert(0, 5)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_es(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Espirito Santo
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_go(self, inscr_est):
        """Checks if company register number is val_check_ieid to Brazilian
        state Goiais
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if not inscr_est[:2] in ['10', '11', '15']:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # define os valores de 'p' e 'd'
        inscr_est_int = int(inscr_est[:8])
        if ( inscr_est_int >= 10103105 ) and ( inscr_est_int <= 10119997 ):
            inscr_est_d = 1
        else:
            inscr_est_d = 0

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        elif r == 1:
            f = inscr_est_d
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
      
    def _validate_ie_ma(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Maranhão
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '12':
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_mg(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Minas Gerais
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 13:
            return False

        # Pega apenas os 11 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:11]

        nova_ie_aux = list(nova_ie)
        nova_ie_aux.insert(3, 0)
        prod = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        r = str([x*y for (x, y) in zip(nova_ie_aux, prod)])
        r = re.sub('[^0-9]', '', r)
        r = map(int, r)
        r = sum(r)
        r2 = (r/10+1)*10
        r = r2 - r
        nova_ie.append(r)

        prod = [3, 2, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
      
    def _validate_ie_ms(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Mato Grosso do Sul
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '28':
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_mt(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Mato Grosso
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 11:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:10]

        prod = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_pa(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Pará
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '15':
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_pb(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Paraíba
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_pe(self, inscr_est):
        """Check if number in insc_est is valid to Brazilian
        state of Pernambuco
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if (len(inscr_est) != 9) and (len(inscr_est) != 14):
            return False

        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 9:

            # Pega apenas os 7 primeiros dígitos da inscrição estadual e
            # gera os dígitos verificadores
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:7]

            prod = [8, 7, 6, 5, 4, 3, 2]
            while len(nova_ie) < 9:
                r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
                if r > 1:
                    f = 11 - r
                else:
                    f = 0
                nova_ie.append(f)
                prod.insert(0, 9)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 14:

            # Pega apenas os 13 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:13]

            prod = [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            f = 11 - r
            if f > 10:
                f = f - 10
            nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
      
    def _validate_ie_pi(self, inscr_est):
        """Check if number in insc_est is valid to Brazilian
        state of Piauí
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_pr(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Rio de Paraná
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 10:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [3, 2, 7, 6, 5, 4, 3, 2]
        while len(nova_ie) < 10:
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r > 1:
                f = 11 - r
            else:
                f = 0
            nova_ie.append(f)
            prod.insert(0, 4)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_rj(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Rio de janeiro
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """
        
        # Limpando a inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 8:
            return False

        # Pega apenas os 12 primeiros dígitos da inscrição estadual e
        # gera os dígitos verificadores
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:7]

        prod = [2, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_rn(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Rio Grande do Norte
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if (len(inscr_est) != 9) and (len(inscr_est) != 10):
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '20':
            return False

        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 9:

            # Pega apenas os 8 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            nova_ie = inscr_est[:8]

            prod = [9, 8, 7, 6, 5, 4, 3, 2]
            r = (sum([x*y for (x, y) in zip(nova_ie, prod)]) * 10) % 11
            if r > 9:
                r = 0
            nova_ie.append(r)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 10:

            # Pega apenas os 9 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            nova_ie = inscr_est[:9]

            prod = [10, 9, 8, 7, 6, 5, 4, 3, 2]
            r = (sum([x*y for (x, y) in zip(nova_ie, prod)]) * 10) % 11
            if r > 9:
                r = 0
            nova_ie.append(r)


        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_ro(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Rondônia
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if (len(inscr_est) != 9) and (len(inscr_est) != 14):
            return False

        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 9:

            # Despreza-se os 3 primeiros dígitos, pega apenas os 8 primeiros
            # dígitos da inscrição estadual e gera o dígito verificador
            nova_ie = inscr_est[3:8]

            prod = [6, 5, 4, 3, 2]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            f = 11 - r
            if f > 9:
                f = f - 10
            nova_ie.append(f)

            nova_ie.insert(0, inscr_est[0])
            nova_ie.insert(1, inscr_est[1])
            nova_ie.insert(2, inscr_est[2])

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 14:

            # Pega apenas os 13 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            nova_ie = inscr_est[:13]

            prod = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            f = 11 - r
            if f > 9:
                f = f - 10
            nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_rr(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Roraima
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando a inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if inscr_est[:2] != '24':
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [1, 2, 3, 4, 5, 6, 7, 8]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 9
        nova_ie.append(r)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_rs(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Rio Grande do Sul
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 10:
            return False

        # Pega apenas os 9 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:9]

        prod = [2, 9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
    
    def _validate_ie_sc(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Santa Catarina
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_se(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Sergipe
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_sp(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state São Paulo
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Industriais e comerciais
        if inscr_est[0] != 'P':

            # Limpando o campo inscrição estadual
            if not inscr_est.isdigit():
                inscr_est = re.sub('[^0-9]', '', inscr_est)

            # verificando o tamanho da inscrição estadual
            if len(inscr_est) != 12:
                return False

            # Pega apenas os 8 primeiros dígitos da inscrição estadual e
            # gera o primeiro dígito verificador
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:8]

            prod = [1, 3, 4, 5, 6, 7, 8, 10]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r < 10:
                f = r
            if r == 10:
                f = 0
            if r == 11:
                f = 1
            nova_ie.append(f)

            # gera o segundo dígito verificador
            nova_ie.append(inscr_est[9])
            nova_ie.append(inscr_est[10])
            prod = [3, 2, 10, 9, 8, 7, 6, 5, 4, 3, 2]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r < 10:
                f = r
            if r == 10:
                f = 0
            if r == 11:
                f = 1
            nova_ie.append(f)

        # Produtor rural
        else:

            # Limpando o campo inscrição estadual
            if not inscr_est.isdigit():
                inscr_est = re.sub('[^0-9]', '', inscr_est)

            # verificando o tamanho da inscrição estadual
            if len(inscr_est) != 12:
                return False

            # verificando o primeiro dígito depois do 'P'
            if inscr_est[0] != '0':
                return False

            # Pega apenas os 8 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:8]

            prod = [1, 3, 4, 5, 6, 7, 8, 10]
            r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
            if r < 10:
                f = r
            if r == 10:
                f = 0
            if r == 11:
                f = 1
            nova_ie.append(f)

            nova_ie.append(inscr_est[9])
            nova_ie.append(inscr_est[10])
            nova_ie.append(inscr_est[11])

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    def _validate_ie_to(self, inscr_est):
        """Checks if company register number is valid to Brazilian
        state Tocantins
        @param self: The object pointer
        @param inscr_est: The company state number value,
        @return: True or False.
        """

        # Limpando o campo inscrição estadual
        if not inscr_est.isdigit():
            inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 11:
            return False

        # verificando os dígitos 3 e 4
        if not inscr_est[2:4] in ['01', '02', '03', '99']:
            return False

        # Pega apenas os dígitos que entram no cálculo
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:2] + inscr_est[4:10]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x*y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        nova_ie.insert(2, inscr_est[2])
        nova_ie.insert(3, inscr_est[3])

        # Se o número gerado coincidir com o número original, é válido
        if nova_ie == inscr_est:
            return True

        return False
     
    _constraints = [
                    (_check_cnpj_cpf, u'CNPJ/CPF invalido!', ['cnpj_cpf']),
                    (_check_ie, u'Inscrição Estadual inválida!', ['inscr_est'])
    ]
    
    _sql_constraints = [
                    ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)', 
                     u'Já existe um parceiro cadastrado com este CPF/CNPJ !'),
                    ('res_partner_inscr_est_uniq', 'unique (inscr_est)', 
                     u'Já existe um parceiro cadastrado com esta Inscrição Estadual/RG !')
    ]

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, tipo_pessoa, cnpj_cpf):
        if not cnpj_cpf or not tipo_pessoa:
            return {}

        import re
        val = re.sub('[^0-9]', '', cnpj_cpf)

        if tipo_pessoa == 'J' and len(val) == 14:            
            cnpj_cpf = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
        
        elif tipo_pessoa == 'F' and len(val) == 11:
            cnpj_cpf = "%s.%s.%s-%s" % (val[0:3], val[3:6], val[6:9], val[9:11])
        
        return {'value': {'tipo_pessoa': tipo_pessoa, 'cnpj_cpf': cnpj_cpf}}
    
res_partner()

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
