#  -*- encoding: utf-8 -*-
# #############################################################################
#                                                                             #
#  Copyright (C) 2012  Renato Lima - Akretion                                 #
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
# #############################################################################

import re
from openerp import models, fields, api, _
from openerp.addons.l10n_br_base.tools import fiscal
from openerp.exceptions import Warning


class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    legal_name = fields.Char(u'Razão Social', size=128,
                             help="Nome utilizado em documentos fiscais")
    cnpj = fields.Char('CNPJ', size=18,  oldname='cnpj_cpf')
    inscr_est = fields.Char('Inscr. Estadual', size=16)
    inscr_mun = fields.Char('Inscr. Municipal', size=18)
    suframa = fields.Char('Suframa', size=18)
    l10n_br_city_id = fields.Many2one('l10n_br_base.city', 'Municipio',
                                      domain="[('state_id','=',state_id)]")
    district = fields.Char('Bairro', size=32)
    number = fields.Char('Número', size=10)
    name_surname = fields.Char(u'Nome e Sobrenome', size=128,
                               help="Nome utilizado em documentos fiscais")
    cpf = fields.Char('CPF', size=18)
    rg = fields.Char('RG', size=16)

    @api.one
    @api.constrains('cnpj')
    def _check_cnpj(self):
        if self.cnpj:
            if not fiscal.validate_cnpj(self.cnpj):
                raise Warning(_(u'CNPJ inválido!'))
        return True

    @api.one
    @api.constrains('cpf')
    def _check_cpf(self):
        if self.cpf:
            if not fiscal.validate_cpf(self.cpf):
                raise Warning(_(u'CPF inválido!'))
        return True

    def _validate_ie_param(self, uf, inscr_est):
        try:
            mod = __import__(
                'openerp.addons.l10n_br_base.tools.fiscal', globals(), locals(), 'fiscal')

            validate = getattr(mod, 'validate_ie_%s' % uf)
            if not validate(inscr_est):
                return False
        except AttributeError:
            if not fiscal.validate_ie_param(uf, inscr_est):
                return False
        return True

    @api.one
    @api.constrains('inscr_est')
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False."""
        if (not self.inscr_est
                or self.inscr_est == 'ISENTO'
                or not self.is_company):
            return True
        uf = (self.state_id and
              self.state_id.code.lower() or '')
        res = self._validate_ie_param(uf, self.inscr_est)
        if not res:
            raise Warning(_(u'Inscrição Estadual inválida!'))
        return True

    @api.onchange('cnpj')
    def onchange_mask_cnpj(self):
        if self.cnpj:
            val = re.sub('[^0-9]', '', self.cnpj)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
                self.cnpj = cnpj_cpf
            else:
                raise Warning(_(u'Verifique o CNPJ'))

    @api.onchange('cpf')
    def onchange_mask_cpf(self):
        if self.cnpj:
            val = re.sub('[^0-9]', '', self.cpf)
            if len(val) == 11:
                cnpj_cpf = "%s.%s.%s-%s"\
                    % (val[0:3], val[3:6], val[6:9], val[9:11])
                self.cpf = cnpj_cpf
            else:
                raise Warning(_(u'Verifique o CPF'))

    @api.onchange('l10n_br_city_id')
    def onchange_l10n_br_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int l10n_br_city_id: id do l10n_br_city_id digitado.

        return: dicionário com o nome e id do município.
        """
        if self.l10n_br_city_id:
            self.city = self.l10n_br_city_id.name
            self.l10n_br_city_id = self.l10n_br_city_id

    @api.v7
    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        result = super(CrmLead, self).on_change_partner(
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

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        id = super(CrmLead, self)._lead_create_contact(
            lead, name, is_company, parent_id)
        value = {
            'number': lead.number,
            'district': lead.district,
            'l10n_br_city_id': lead.l10n_br_city_id.id
        }
        if is_company:
            value.update({
                'legal_name': lead.legal_name,
                'cnpj_cpf': lead.cnpj,
                'inscr_est': lead.inscr_est,
                'inscr_mun': lead.inscr_mun,
                'suframa': lead.suframa,
                })
        else:
            value.update({
                'legal_name': lead.name_surname,
                'cnpj_cpf': lead.cpf,
                'inscr_est': lead.rg,
                })
        if id:
            partner = self.env['res.partner'].browse(id)
            partner[0].write(value)
        return id
