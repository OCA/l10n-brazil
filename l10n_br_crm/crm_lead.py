# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2012  Renato Lima - Akretion                                  #
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
from osv import fields, orm
from l10n_br_base.tools import fiscal


class crm_lead(orm.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    _columns = {
        'legal_name': fields.char(u'Razão Social', size=128,
                                   help="nome utilizado em "
                                   "documentos fiscais"),
        'cnpj_cpf': fields.char('CNPJ/CPF', size=18),
        'inscr_est': fields.char('Inscr. Estadual/RG', size=16),
        'inscr_mun': fields.char('Inscr. Municipal', size=18),
        'suframa': fields.char('Suframa', size=18),
        'l10n_br_city_id': fields.many2one(
            'l10n_br_base.city', 'Municipio',
            domain="[('state_id','=',state_id)]"),
        'district': fields.char('Bairro', size=32),
        'number': fields.char('Número', size=10)
    }

    def _check_cnpj_cpf(self, cr, uid, ids):

        for partner in self.browse(cr, uid, ids):
            if not partner.cnpj_cpf:
                continue

            if partner.partner_name:
                if not fiscal.validate_cnpj(partner.cnpj_cpf):
                    return False
            elif not fiscal.validate_cpf(partner.cnpj_cpf):
                    return False

        return True

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
                or not partner.partner_name:
                continue

            uf = partner.state_id and \
            partner.state_id.code.lower() or ''

            try:
                mod = __import__(
                'l10n_br_base.tools.fiscal', globals(), locals(), 'fiscal')

                validate = getattr(mod, 'validate_ie_%s' % uf)
                if not validate(partner.inscr_est):
                    return False
            except AttributeError:
                if not fiscal.validate_ie_param(uf, partner.inscr_est):
                    return False

        return True

    _constraints = [
        (_check_cnpj_cpf, u'CNPJ/CPF invalido!', ['cnpj_cpf']),
        (_check_ie, u'Inscrição Estadual inválida!', ['inscr_est'])
    ]

    def onchange_mask_cnpj_cpf(self, cr, uid, ids, partner_name, cnpj_cpf):
        result = {'value': {}}
        if cnpj_cpf:
            val = re.sub('[^0-9]', '', cnpj_cpf)
            if partner_name and len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            elif not partner_name and len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                % (val[0:3], val[3:6], val[6:9], val[9:11])
            result['value'].update({'cnpj_cpf': cnpj_cpf})
        return result

    def onchange_mask_zip(self, cr, uid, ids, code_zip):

        result = {'value': {'zip': False}}
        if not code_zip:
            return result

        val = re.sub('[^0-9]', '', code_zip)
        if len(val) == 8:
            code_zip = "%s-%s" % (val[0:5], val[5:8])
            result['value']['zip'] = code_zip
        return result

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        result = super(crm_lead, self).on_change_partner(
            cr, uid, ids, partner_id, context)

        if partner_id:
            partner = self.pool.get('res.partner').browse(
                cr, uid, partner_id, context=context)
            result['value']['legal_name'] = partner.legal_name
            result['value']['cnpj_cpf'] = partner.cnpj_cpf
            result['value']['inscr_est'] = partner.inscr_est
            result['value']['suframa'] = partner.suframa
            result['value']['number'] = partner.number
            result['value']['district'] = partner.district
            result['value']['l10n_br_city_id'] = partner.l10n_br_city_id.id

        return result

    def _lead_create_contact(self, cr, uid, lead, name, is_company,
                            parent_id=False, context=None):
        result = super(crm_lead, self)._lead_create_contact(
            cr, uid, lead, name, is_company, parent_id, context)

        value = {
            'number': lead.number,
            'district': lead.district,
            'l10n_br_city_id': lead.l10n_br_city_id.id
        }

        if is_company:
            value = {
                'legal_name': lead.legal_name,
                'cnpj_cpf': lead.cnpj_cpf,
                'inscr_est': lead.inscr_est,
                'inscr_mun': lead.inscr_mun,
                'suframa': lead.suframa,
            }

        self.pool.get('res.partner').write(
            cr, uid, [result], value, context=context)
        return result
