# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 Gabriel C. Stabel                                        #
# Copyright (C) 2009-2012  Renato Lima (Akretion)                             #
# Copyright (C) 2012 Raphaël Valyi (Akretion)                                 #
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

import re
from osv import osv, fields


PARAMETERS = {
    'ac': {'tam': 13, 'val_tam': 11, 'starts_with': '01'},
    'al': {'tam': 9, 'starts_with': '24'},
    'am': {'tam': 9},
    'ce': {'tam': 9},
    'df': {'tam': 13, 'val_tam': 11, 'starts_with': '07'},
    'es': {'tam': 9},
    'ma': {'tam': 9, 'starts_with': '12'},
    'mt': {'tam': 11, 'prod': [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]},
    'ms': {'tam': 9, 'starts_with': '28'},
    'pa': {'tam': 9, 'starts_with': '15'},
    'pb': {'tam': 9},
    'pr': {'tam': 10, 'val_tam': 8, 'prod': [3, 2, 7, 6, 5, 4, 3, 2]},
    'pi': {'tam': 9},
    'rj': {'tam': 8, 'prod': [2, 7, 6, 5, 4, 3, 2]},
    'rn': {'tam': 10, 'val_tam':  9,  'prod': [10, 9, 8, 7, 6, 5, 4, 3, 2]},
    'rs': {'tam': 10},
    'rr': {'tam': 9, 'starts_with': '24', 'prod': [1, 2, 3, 4, 5, 6, 7, 8],
           'div': 9},
    'sc': {'tam': 9},
    'se': {'tam': 9}}


class res_partner(osv.Model):
    _inherit = 'res.partner'

    def _display_address(self, cr, uid, address,
                         without_company=False, context=None):
        if address.country_id and address.country_id.code != 'BR':
            #this ensure other localizations could do what they want
            return super(res_partner,
                         self)._display_address(cr, uid, address,
                                                without_company=False,
                                                context=None)
        else:
            address_format = address.country_id and \
            address.country_id.address_format or \
            "%(street)s\n%(street2)s\n%(city)s %(state_code)s"
            "%(zip)s\n%(country_name)s"
            args = {
                'state_code': address.state_id and address.state_id.code or '',
                'state_name': address.state_id and address.state_id.name or '',
                'country_code': address.country_id and \
                address.country_id.code or '',
                'country_name': address.country_id and \
                address.country_id.name or '',
                'company_name': address.parent_id and \
                address.parent_id.name or '',
                'l10n_br_city_name': address.l10n_br_city_id and \
                address.l10n_br_city_id.name or '',
                'state_code': address.state_id and address.state_id.code or ''
            }
            address_field = ['title', 'street', 'street2', 'zip', 'city',
                             'number', 'district']
            for field in address_field:
                args[field] = getattr(address, field) or ''
            if without_company:
                args['company_name'] = ''
            elif address.parent_id:
                address_format = '%(company_name)s\n' + address_format
            return address_format % args

    def _get_partner(self, cr, uid, ids, context=None):
        result = {}
        for partner_addr in self.pool.get('res.partner').browse(
            cr, uid, ids, context=context):
            result[partner_addr.parent_id.id] = True
        return result.keys()

    def _address_default_fs(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = {'addr_fs_code': False}

            partner_addr = self.pool.get('res.partner').address_get(
                cr, uid, [partner.id], ['invoice'])
            #TODO shouldn't we get the default one if no invoice one is found?

            if partner_addr:
                partner_addr_default = self.pool.get('res.partner')\
                .browse(cr, uid, [partner_addr['invoice']])[0]
                addr_fs_code = partner_addr_default.state_id\
                and partner_addr_default.state_id.code or ''
                res[partner.id]['addr_fs_code'] = addr_fs_code.lower()

        return res

    _columns = {
<<<<<<< HEAD
<<<<<<< HEAD
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
        'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
        'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
        'inscr_mun': fields.char('Inscr. Municipal', size=18),
        'suframa': fields.char('Suframa', size=18),
        'legal_name': fields.char('Razão Social', size=128,
                                   help="nome utilizado em "
                                   "documentos fiscais"),
        'addr_fs_code': fields.function(
            _address_default_fs,
            method=True,
            string='Address Federal State Code',
            type="char", size=2,
            multi='all',
            store={
                   'res.partner': (
                                   _get_partner,
                                   ['country_id', 'state_id'], 20), }),

        # address fields:
        'l10n_br_city_id':\
        fields.many2one('l10n_br_base.city', 'Municipio',\
                        domain="[('state_id','=',state_id)]"),
        'district': fields.char('Bairro', size=32),
        'number': fields.char('Número', size=10)
                }

    def _check_cnpj_cpf(self, cr, uid, ids):

        for partner in self.browse(cr, uid, ids):
            if not partner.cnpj_cpf:
                continue

            if partner.is_company:
                if not self._validate_cnpj(partner.cnpj_cpf):
                    return False
            elif not self._validate_cpf(partner.cnpj_cpf):
                    return False

        return True

    def _validate_cnpj(self, cnpj):
        """ Rotina para validação do CNPJ - Cadastro Nacional
        de Pessoa Juridica.

        :param string cnpj: CNPJ para ser validado

        :return bool: True or False
        """
        # Limpando o cnpj
        if not cnpj.isdigit():
            cnpj = re.sub('[^0-9]', '', cnpj)

        # verificando o tamano do  cnpj
        if len(cnpj) != 14:
            return False

        # Pega apenas os 12 primeiros dígitos do CNPJ e gera os digitos
        cnpj = map(int, cnpj)
        novo = cnpj[:12]

        prod = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        while len(novo) < 14:
            r = sum([x * y for (x, y) in zip(novo, prod)]) % 11
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
        """Rotina para validação do CPF - Cadastro Nacional
        de Pessoa Física.

        :Return: True or False

        :Parameters:
          - 'cpf': CPF to be validate.
        """
        if not cpf.isdigit():
            cpf = re.sub('[^0-9]', '', cpf)

        if len(cpf) != 11:
            return False

        # Pega apenas os 9 primeiros dígitos do CPF e gera os 2 dígitos
        cpf = map(int, cpf)
        novo = cpf[:9]

        while len(novo) < 11:
            r = sum([(len(novo) + 1 - i) * v for i, v in enumerate(novo)]) % 11

            if r > 1:
                f = 11 - r
            else:
                f = 0
            novo.append(f)

        # Se o número gerado coincidir com o número original, é válido
        if novo == cpf:
            return True

        return False

    def _validate_ie_param(self, uf, inscr_est):

        if not uf in PARAMETERS:
            return True

        tam = PARAMETERS[uf].get('tam', 0)

        inscr_est = unicode(inscr_est).strip().rjust(int(tam), u'0')

        inscr_est = re.sub('[^0-9]', '', inscr_est)

        val_tam = PARAMETERS[uf].get('val_tam', tam - 1)
        if isinstance(tam, list):
            i = tam.find(len(inscr_est))
            if i == -1:
                return False
            else:
                val_tam = val_tam[i]
        else:
            if len(inscr_est) != tam:
                return False

        sw = PARAMETERS[uf].get('starts_with', '')
        if not inscr_est.startswith(sw):
            return False

        inscr_est_ints = [int(c) for c in inscr_est]
        nova_ie = inscr_est_ints[:val_tam]

        prod = PARAMETERS[uf].get('prod', [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        prod = prod[-val_tam:]
        while len(nova_ie) < tam:
            r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % PARAMETERS[uf]\
            .get('div', 11)

            if r > 1:
                f = 11 - r
            else:
                f = 0

            if not uf in 'rr':
                nova_ie.append(f)
            else:
                nova_ie.append(r)
            prod.insert(0, prod[0] + 1)

        # Se o número gerado coincidir com o número original, é válido
        return nova_ie == inscr_est_ints

    def _check_ie(self, cr, uid, ids):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.

        :Parameters:
            - 'cr': Database cursor.
            - 'uid': Current user’s ID for security checks.
            - 'ids': List of partner objects IDs.
        """
        for partner in self.browse(cr, uid, ids):
            if not partner.inscr_est \
                or partner.inscr_est == 'ISENTO' \
                or not partner.is_company:
                continue

            uf = partner.addr_fs_code
            try:
                validate = getattr(self, '_validate_ie_%s' % uf)
                if not validate(partner.inscr_est):
                    return False
            except AttributeError:
                if not self._validate_ie_param(uf, partner.inscr_est):
                    return False

        return True

    def _validate_ie_ap(self, inscr_est):
        inscr_est = re.sub('[^0-9]', '', inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) != 9:
            return False

        # verificando os dois primeiros dígitos
        if not inscr_est.startswith('03'):
            return False

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # define os valores de 'p' e 'd'
        inscr_est_int = int(inscr_est[:8])
        if inscr_est_int <= 3017000:
            inscr_est_p = 5
            inscr_est_d = 0
        elif inscr_est_int <= 3019022:
            inscr_est_p = 9
            inscr_est_d = 1
        else:
            inscr_est_p = 0
            inscr_est_d = 0

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = (inscr_est_p + sum([x * y for (x, y) in zip(nova_ie, prod)])) % 11
        if r > 1:
            f = 11 - r
        elif r == 1:
            f = 0
        else:
            f = inscr_est_d
        nova_ie.append(f)

        return nova_ie == inscr_est

    def _validate_ie_ba(self, inscr_est):
        inscr_est = re.sub('[^0-9]', '', inscr_est)
        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 8:
            tam = 8
            val_tam = 6
            test_digit = 0
        elif len(inscr_est) == 9:
            tam = 9
            val_tam = 7
            test_digit = 1
        else:
            return False

        nova_ie = inscr_est[:val_tam]

        prod = [8, 7, 6, 5, 4, 3, 2][-val_tam:]

        if inscr_est[test_digit] in [0, 1, 2, 3, 4, 5, 8]:
            modulo = 10
        else:
            modulo = 11

        while len(nova_ie) < tam:
            r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % modulo
            if r > 0:
                f = modulo - r
            else:
                f = 0

            if len(nova_ie) == val_tam:
                nova_ie.append(f)
            else:
                nova_ie.insert(val_tam, f)
            prod.insert(0, prod[0] + 1)

        return nova_ie == inscr_est

    def _validate_ie_go(self, inscr_est):
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
        if inscr_est_int >= 10103105 and inscr_est_int <= 10119997:
            inscr_est_d = 1
        else:
            inscr_est_d = 0

        # Pega apenas os 8 primeiros dígitos da inscrição estadual e
        # gera o dígito verificador
        inscr_est = map(int, inscr_est)
        nova_ie = inscr_est[:8]

        prod = [9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        elif r == 1:
            f = inscr_est_d
        else:
            f = 0
        nova_ie.append(f)

        return nova_ie == inscr_est

    def _validate_ie_mg(self, inscr_est):
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
        r = str([x * y for (x, y) in zip(nova_ie_aux, prod)])
        r = re.sub('[^0-9]', '', r)
        r = map(int, r)
        r = sum(r)
        r2 = (r / 10 + 1) * 10
        r = r2 - r

        if r >= 10:
            r = 0

        nova_ie.append(r)

        prod = [3, 2, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        return nova_ie == inscr_est

    def _validate_ie_pe(self, inscr_est):
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
                r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
                if r > 1:
                    f = 11 - r
                else:
                    f = 0
                nova_ie.append(f)
                prod.insert(0, 9)
        elif len(inscr_est) == 14:

            # Pega apenas os 13 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:13]

            prod = [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2]
            r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
            f = 11 - r
            if f > 10:
                f = f - 10
            nova_ie.append(f)

        return nova_ie == inscr_est

    def _validate_ie_ro(self, inscr_est):
        def gera_digito_ro(nova_ie, prod):
            r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
            f = 11 - r
            if f > 9:
                f = f - 10
            return f

        inscr_est = re.sub('[^0-9]', '', inscr_est)
        inscr_est = map(int, inscr_est)

        # verificando o tamanho da inscrição estadual
        if len(inscr_est) == 9:
            # Despreza-se os 3 primeiros dígitos, pega apenas os 8 primeiros
            # dígitos da inscrição estadual e gera o dígito verificador
            nova_ie = inscr_est[3:8]

            prod = [6, 5, 4, 3, 2]
            f = gera_digito_ro(nova_ie, prod)
            nova_ie.append(f)

            nova_ie = inscr_est[0:3] + nova_ie
        elif len(inscr_est) == 14:
            # Pega apenas os 13 primeiros dígitos da inscrição estadual e
            # gera o dígito verificador
            nova_ie = inscr_est[:13]

            prod = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            f = gera_digito_ro(nova_ie, prod)
            nova_ie.append(f)
        else:
            return False

        return nova_ie == inscr_est

    def _validate_ie_sp(self, inscr_est):
        def gera_digito_sp(nova_ie, prod):
            r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
            if r < 10:
                return r
            elif r == 10:
                return 0
            else:
                return 1

        # Industriais e comerciais
        if inscr_est[0] != 'P':

            inscr_est = re.sub('[^0-9]', '', inscr_est)

            # verificando o tamanho da inscrição estadual
            if len(inscr_est) != 12:
                return False

            # Pega apenas os 8 primeiros dígitos da inscrição estadual e
            # gera o primeiro dígito verificador
            inscr_est = map(int, inscr_est)
            nova_ie = inscr_est[:8]

            prod = [1, 3, 4, 5, 6, 7, 8, 10]
            f = gera_digito_sp(nova_ie, prod)
            nova_ie.append(f)

            # gera o segundo dígito verificador
            nova_ie.extend(inscr_est[9:11])
            prod = [3, 2, 10, 9, 8, 7, 6, 5, 4, 3, 2]
            f = gera_digito_sp(nova_ie, prod)
            nova_ie.append(f)

        # Produtor rural
        else:
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
            f = gera_digito_sp(nova_ie, prod)
            nova_ie.append(f)

            nova_ie.extend(inscr_est[9:])

        return nova_ie == inscr_est

    def _validate_ie_to(self, inscr_est):
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
        r = sum([x * y for (x, y) in zip(nova_ie, prod)]) % 11
        if r > 1:
            f = 11 - r
        else:
            f = 0
        nova_ie.append(f)

        nova_ie = nova_ie[:2] + inscr_est[2:4] + nova_ie[2:]

        return nova_ie == inscr_est

    _constraints = [
                    (_check_cnpj_cpf, u'CNPJ/CPF invalido!', ['cnpj_cpf']),
                    (_check_ie, u'Inscrição Estadual inválida!',
                     ['inscr_est'])]

    _sql_constraints = [
        ('res_partner_cnpj_cpf_uniq', 'unique (cnpj_cpf)',
         u'Já existe um parceiro cadastrado com este CPF/CNPJ !'),
        ('res_partner_inscr_est_uniq', 'unique (inscr_est)',
         u'Já existe um parceiro cadastrado com esta Inscrição Estadual/RG !')]

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, is_company, cnpj_cpf):
        res = super(res_partner, self).onchange_type(self, cr, uid, ids, \
                                                     is_company)
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if is_company and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif not is_company and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
            res['value'].update({'cnpj_cpf': cnpj_cpf})
        return res

    #TODO migrate
    def onchange_l10n_br_city_id(self, cr, uid, ids, l10n_br_city_id):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int l10n_br_city_id: id do l10n_br_city_id digitado.

        return: dicionário com o nome e id do município.
        """
        result = {'value': {'city': False, 'l10n_br_city_id': False}}

        if not l10n_br_city_id:
            return result

        obj_city = self.pool.get('l10n_br_base.city').read(
            cr, uid, l10n_br_city_id, ['name', 'id'])

        if obj_city:
            result['value']['city'] = obj_city['name']
            result['value']['l10n_br_city_id'] = obj_city['id']

        return result

    #TODO migrate
    def onchange_mask_zip(self, cr, uid, ids, zip):

        result = {'value': {'zip': False}}

        if not zip:
            return result

        val = re.sub('[^0-9]', '', zip)

        if len(val) == 8:
            zip = "%s-%s" % (val[0:5], val[5:8])
            result['value']['zip'] = zip
        return result


class res_partner_bank(osv.Model):
    """ Adiciona campos necessários para o cadastramentos de contas
    bancárias na brasil.
    """
    _inherit = 'res.partner.bank'
    _columns = {
        'acc_number': fields.char('Account Number', size=64, required=False),
        'bank': fields.many2one('res.bank', 'Bank', required=False),
        'acc_number_dig': fields.char("Digito Conta", size=8),
        'bra_number': fields.char("Agência", size=8),
        'bra_number_dig': fields.char("Dígito Agência", size=8)}
